import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import load_dataset
import numpy as np
from sklearn.metrics import accuracy_score, f1_score

MODEL_NAME = "GroNLP/hateBERT"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)

data_files = {"data": "../data/balanced_train.csv"}
dataset = load_dataset("csv", data_files=data_files)
dataset = dataset["data"].train_test_split(test_size=0.2, seed=42)

dataset = dataset.filter(lambda example: example["Content"] is not None and example["Content"] != "")

small_train_dataset = dataset["train"].shuffle(seed=42).select(range(500))
small_eval_dataset = dataset["test"].shuffle(seed=42).select(range(100))
small_dataset = {"train": small_train_dataset, "test": small_eval_dataset}

def tokenize_function(examples):
    tokenized = tokenizer(
        examples["Content"],
        truncation=True,
        padding="max_length",
        max_length=128
    )
    tokenized["labels"] = examples["Label"]
    return tokenized

tokenized_datasets = small_dataset.copy()
for split in tokenized_datasets:
    tokenized_datasets[split] = tokenized_datasets[split].map(
        tokenize_function, batched=True, remove_columns=["Content"]
    )

# accuracy and f1 for now
def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    acc = accuracy_score(labels, preds)
    f1 = f1_score(labels, preds, average="weighted")
    return {"accuracy": acc, "f1": f1}

training_args = TrainingArguments(
    output_dir="./hatebert_finetuned",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16, 
    per_device_eval_batch_size=16,
    num_train_epochs=1,
    max_steps=100,
    weight_decay=0.01,
    logging_dir="./logs",
    save_total_limit=2,
    load_best_model_at_end=True,
    fp16=True if torch.cuda.is_available() else False,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["test"],
    compute_metrics=compute_metrics,
)

def main():
    trainer.train()
    
    # save the fine-tuned model and tokenizer for later inference
    trainer.save_model("./hatebert_finetuned")
    tokenizer.save_pretrained("./hatebert_finetuned")
    print("Model fine-tuning complete and saved to './hatebert_finetuned'.")

if __name__ == "__main__":
    main()