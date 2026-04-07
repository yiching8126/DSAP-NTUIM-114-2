# Project Proposal: LedgerLogic CLI

## 1. Project Title, Motivation, and Goals
* **Project Title:** LedgerLogic CLI
* **Motivation:** Managing personal finances often involves bulky GUI applications or privacy-invasive mobile apps. For developers, a Command Line Interface (CLI) tool provides a fast, keyboard-centric way to track expenses and income without leaving the terminal. We aim to create a one-stop service for users to fincancial recording. 
* **Goals:** * To create a robust, lightweight tool for personal bookkeeping.
    * To implement efficient and robust data storage and retrieval systems.
    * To apply data structures learned in class to organize financial transactions by date and category.

## 2. Expected Features
* **Transaction Management:** Add, delete, and edit income/expense records.
* **Category Tagging:** Users can tag transactions (e.g., #food, #rent, #salary) to categorize them. 
* **Persistence:** Save data to a local file (JSON or CSV) so it persists between sessions, and can be exported/imported to other devices. 
* **Query & Statistics:** * Filter transactions by date range.
    * Generate a monthly summary of total income vs. total expenses.
* **Sorting:** View transactions sorted by date or amount.

## 3. Techniques and Languages
* **Programming Language:** Python
* **Libraries:** 
    * json: to export transactions into a file
    * argparse, cmd: to read input from commandline
    * datatime, decimal: for accounting transaction deatails. 
    * rich, for making UI.
    * PyInstaller: to wrap the python file into an executable file, for compatibility.
* **Version Control:** GitHub (as per course requirements).

## 4. Expected Schedule
* **Week 7-8:** Implement: Command parsing; Design: json structure for transactions. 
    * **command: transaction:** *[command] [dr_account_name] [dr_amount] [cr_account_name] [cr_amount].*
    * **command: simple_expense:** *[command] [dr_account_name] [dr_amount]*
    *(automatically deducts cash from user's account.)*
    * (When testing, generate random legal transaction strings and test.)
    *(ambitious optional goal: implement some way to understand typos)
        * at the very least, if the user input is "malformed", then we will ask the user to re-input.
        * [ambitious goal: typo handling] There is a way to understand typos. For example: user says he purchased "hamborgor", and there's something called "Levenshtein Distance" that enables us to determine the similarity of two strings (we can compare user input to all legal inputs), and then we can infer the intended input from a typo.
* **Week 9-10:** Implement basic CRUD (Create, Read, Update, Delete) operations for transactions. Add an "alias" feature that lets the user run the command by inputting some "abbreviation" (if possible).
    * **command: export_record **
    *The user will then be prompted to save new file*
    * **command: import_record**
    *Prompts user to open file, and then imports record.*
    * *(the program will automatically make a file (transaction log, in the folder where the ) will automatically update a transaction log by appending new transactions on the back of the file)*
    * [command: delete]
     *(opens something that makes the user choose which transaction to delete)*
* **Week 11-12 (Prototype):** Finalize file persistence and implement basic filtering logic. Also, add a help menu that introduces the commands to the user, like in windows CMD. And, add some macros to automate tasks (if possible). 
    *add: sort transactions by [date or transaction_amount]
    *add: [command: help]
* **Week 13-14:** Implement transaction summaries and UI formatting (tables). Implement exception handling. 
* **Week 15:** Final testing, bug fixes, and recording the Demo video. The demo video might include:
    * me advertising this accounting app
    * footage of the program working, including (but not limited to)
        * add/delete transaction
        * export/import records
        * T-account analysis (for example, the T-account of "cash" would show the effects of all transactions involving "cash", this is useful for knowing if you're gaining profit or not)
        * typo handling, macros (if implemented)
    * explaining how I endsured that the program is indeed functioning, and is capable of reliably keeping financial records

## 5. Connection to DSAP Course
This project will involve several core concepts from **Data Structures and Advanced Programming**:

* **Data Structures:** 
    * **Linked Lists or Dynamic Arrays:** To store a sequence of transactions in memory during a session.
    * **Hash Maps / Dictionaries:** To group transactions by categories efficiently for the statistics feature.
* **Sorting Algorithms:** To implement the "sort by amount" or "sort by date" functionality, comparing different sorting efficiencies (e.g., Quicksort vs. Mergesort for larger datasets).
* **File I/O & Serialization:** Applying advanced programming techniques to handle data persistence and error handling when reading from/writing to disk.