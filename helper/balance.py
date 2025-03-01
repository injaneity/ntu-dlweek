# Code to solve imbalanced dataset issue by including equal number of hate and non-hate comments
from datasets import load_dataset, concatenate_datasets

# Load the dataset from CSV (adjust path/column names if necessary)
data_files = {"data": "../data/train.csv"}
dataset = load_dataset("csv", data_files=data_files)
dataset = dataset["data"]

# Check initial counts (optional)
print("Total examples:", len(dataset))

# Filter examples for each label (assuming 'Label' column contains 0 or 1)
label0_dataset = dataset.filter(lambda example: example["Label"] == 0)
label1_dataset = dataset.filter(lambda example: example["Label"] == 1)

print("Label 0 count:", len(label0_dataset))
print("Label 1 count:", len(label1_dataset))

# Determine the minimum count among the two labels
min_count = min(len(label0_dataset), len(label1_dataset))
print("Using", min_count, "examples for each label for balancing.")

# Downsample each subset to min_count examples (shuffling for randomness)
balanced_label0 = label0_dataset.shuffle(seed=42).select(range(min_count))
balanced_label1 = label1_dataset.shuffle(seed=42).select(range(min_count))

# Concatenate and shuffle the balanced subsets
balanced_dataset = concatenate_datasets([balanced_label0, balanced_label1]).shuffle(seed=42)
print("Balanced dataset count:", len(balanced_dataset))

balanced_dataset.to_csv("../data/balanced_train.csv", index=False)