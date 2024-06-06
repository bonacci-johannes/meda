# Intro
This repository contains the bare meda tool.
Soonly we will provide a reference to a publication about this tool and add public examples how to use it.


# Meda Data transformation Pipeline
## Step 1: Reading Source Data:

The pipeline begins by reading raw source data in a flat structure, where each value occupies its own column, similar to how clinical surveys are currently organized.

## Step 2: Data Class Organization:

The flat data is organized into nested data classes, which correspond to SQL-tables. When defining the data classes, you specify which fields should compute the target variable, and you can provide transformers in the form of Python functions.

## Step 3: Data Class Factory:

The data class factory populates the nested data classes from the flat data structure.

## Step 4: DTO (Data-Transfer-Object) Factory:

The DTO factory translates the nested data classes into DTOs that mirror the SQL structure.

## Step 5: DTO Registry:

The DTO registry manages the DTO factory and database connection. It generates a DTO from a data class and writes it to the database.