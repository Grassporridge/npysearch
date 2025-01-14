from _npysearch import *
import os
from time import localtime, strftime


def cigarString(query, target):
    """
    Generates cigar string from query and target sequences, with '-'s 
    for gaps in alignment

    Input
    -----
    query     = str, with '-' for gap in alignment
    target    = str, same size as query, with '-' for gap in alignment
    
    Output
    ------
    cigar     = str, cigar string with integer (count) followed by one
                of 'X' (mutation), 'D' (gap), or '=' (match)
    """

    # Ensuring that query and target lengths are equal
    assert len(query) == len(target), "Query and Target strings need to be of the same size."

    # Checking of mismatches
    alignment = "".join(["|" if query[i]==target[i] else " " for i in range(len(query))])
    
    # Modifying alignment so that it contains - for gaps instead of 
    # blank space
    alignment = "".join([alignment[i] if query[i] != "-" else query[i] for i in range(len(alignment))])
    alignment = "".join([alignment[i] if target[i] != "-" else target[i] for i in range(len(alignment))])

    flag = alignment[0]
    counter = 0
    matcher = {"|" : "=", " " : "X", "-" : "D"}
    cigar = ""
    for i, character in enumerate(alignment):
        if character == flag:
            counter +=1
        else:
            cigar = cigar + str(counter) + matcher[flag]
            flag = character
            counter = 1
    cigar = cigar + str(counter) + matcher[flag]
        
    return cigar

def readFasta(filepath):
    """
    Simple FASTA file reader

    Input
    -----
    filepath  = str, path to the fasta file to be read
    
    Output
    ------
    sequences = dict, keys = sequence id, values = sequence. Both keys
                and values are strings.
    """

    # Ensure file exists
    if not os.path.isfile(filepath):
        raise IOError("File does not exist.")

    sequences = {}
    with open(filepath, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.strip()[0] == ">":
                current_sequence = line.strip()[1:]
                sequences[current_sequence] = ""
            elif line.strip() == "":
                continue
            else:
                sequences[current_sequence] += line.strip()

    return sequences

def writeFasta(filepath, sequences, wrapAfter = 0):
    """
    Simple FASTA file writer. Use wrapAfter to have sequences wrap 
    after a given number of characters.
    
    Input
    -----
    filepath  = str, path to the fasta file to be written
    sequences = dict, keys = sequence id, values = sequence. Both keys
                and values are strings.
    wrapAfter = int, whole number indicating number of characters in 
                each line of sequence in the file. 
                0 indicates no wrapping. (Default = 0)
    
    Output
    ------
    None
    """
    
    # Check that wrapAfter is a whole number
    assert isinstance(wrapAfter, int) and wrapAfter >= 0, "wrapAfter must be a whole number of type int."

    with open(filepath, 'w') as f:
        # No Wrapping
        if wrapAfter == 0:
            for sequence_name in sequences.keys():
                f.write("> " + sequence_name + "\n")
                f.write(sequences[sequence_name] + "\n")
        # Wrapping
        else:
            for sequence_name in sequences.keys():
                f.write("> " + sequence_name + "\n")
                indices = list(range(0, len(sequences[sequence_name], wrapAfter))) + [-1]
                for i in range(len(indices)-1):
                    f.write(sequences[sequence_name][indices[i]:indices[i+1]] + "\n")

    return None

def writeCSV(filepath, csvPath):
    """
    Function to read the text output file from the dna_blast and 
    protein_blast functions written in C++
    
    Input
    -----
    filepath  = str, path to the output file, written by dna_blast
                or protein_blast
    csvPath   = str, path to the csv output file to be written
    
    Output
    ------
    None
    """
    
    # Column names for the csv file
    header = ["QueryId", "TargetId", "QueryMatchStart",
              "QueryMatchEnd", "TargetMatchStart", "TargetMatchEnd",
              "QueryMatchSeq", "TargetMatchSeq", "NumColumns", "NumMatches",
              "NumMismatches", "NumGaps", "Identity", "Alignment"]

    # Reading the output file line by line and writing it to csv
    with open(csvPath, "w") as csvFile:
        csvFile.write(",".join(header) + "\n")
        with open(filepath, "r") as f:
            row = [None] * 14
            for i, line in enumerate(f):
                if i%13==4:
                    row[0] = line.strip().split()[2][1:].strip()
                    row[1] = line.strip().split()[2][1:].strip()
                if i%13==7:
                    row[2] = line.strip().split()[1].strip()
                    row[3] = line.strip().split()[-1].strip()
                    row[6] = line.strip().split()[3].strip()
                    start = line.index("+") + 2
                if i%13==9:
                    row[4] = line.strip().split()[1].strip()
                    row[5] = line.strip().split()[-1].strip()
                    row[7] = line.strip().split()[3].strip()
                if i%13==11:
                    row[8] = line.split()[0].strip()
                    row[9] = line.split()[2].strip()
                    row[10] = str(int(row[8]) - int(row[9]))
                    row[11] = line.split()[5].strip()
                    row[12] = str(float(line.split()[4][1:-3])/100)
                    # row[13] = "-"
                    row[13] = cigarString(query = row[6], target = row[7])
                if i%13==12:
                    csvFile.write(",".join(row) + "\n")
                    row = [None] * 14

    return None

def readCSV(filepath):
    """
    Simple CSV reader function required for blast function to output
    results as a dictionary

    Input
    -----
    filepath   = str, path to the CSV file containing blast results
    
    Output
    ------
    dictionary = dict, keys = column names, values = columns. 
                 Contains 5 str, 8 int, and 1 float columns.
    """

    with open(filepath, "r") as f:
        # Column names
        header = f.readline().strip().split(",")
        
        # Rest of the results as a list of lists
        data = [line.strip().split(",") for line in f.readlines()]
        #Transposing the list of lists
        data = list(map(list, zip(*data)))

        # Converting type for the int and float columns
        intIndices = [2,3,4,5,8,9,10,11]
        data = [list(map(int, column)) if i in intIndices else column for i,column in enumerate(data)]
        floatIndices = [12]
        data = [list(map(float, column)) if i in floatIndices else column for i,column in enumerate(data)]

        # Creating the dictionary
        dictionary = dict(zip(header, data))

    return dictionary



def blast(query, database, maxAccepts = 1, maxRejects = 16, 
          minIdentity = 0.75, alphabet = "nucleotide", strand = "both",
          outputToFile = False):
    """
    Runs BLAST sequence comparison algorithm

    Input
    -----
    query        = dict or str. Either a dictionary of sequences with 
                   sequence ids as keys and sequences as values, or a
                   path str to the fasta file containing the sequences
    database     = dict or str. Either a dictionary of sequences with
                   sequence ids as keys and sequences as values, or a
                   path str to the fasta file containing the sequences
    maxAccepts   = int, number specifying the maximum accepted hits 
                   (Default = 1)
    maxRejects   = int, number specifying the maximum rejected hits 
                   (Default = 16)
    minIdentity  = float, number specifying the minimal accepted 
                   sequence similarity between the query and database
                   sequences (Default = 0.75)
    alphabet     = str, "nucleotide" or "protein" to specify the query
                   and database alphabet (Default = "nucleotide")
    strand       = str, specify the strand to search: "plus", "minus",
                   or "both". Only affects nucleotide searches. 
                   (Default = "both")
    outputToFile = boolean, set to True to get the results table as a
                   csv file in the working directory and False to 
                   return the results as a dictionary of lists
                   (Default = False)
    
    Output
    ------
    table        = dict of lists, results table in the form of a dict
                   of lists with column names as keys and columns as 
                   values. Contains 5 str, 8 int, and 1 float columns.
                   Can be converted easily to a pandas dataframe using
                   pandas.DataFrame.from_dict()
        OR

    csvPath      = str, path to the csv file containing the results, 
                   stored in the working directory
    """

    startTime = strftime("%Y-%m-%d-%H:%M:%S", localtime())
    
    # Checking what form the query was input in
    # str for path to fasta file and dict for sequences
    # If dict, write to file
    if type(query) == str:
        queryPath = query
        # Ensure file exists
        if not os.path.isfile(queryPath):
            raise IOError("Query file does not exist.")

    elif type(query) == dict:
        queryPath = "query_" + startTime + ".fasta"
        writeFasta(queryPath, query)
    
    else:
        raise TypeError("query must be of type string or dict")

    # Checking what form the database was input in
    # str for path to fasta file and dict for sequences
    # If dict, write to file
    if type(database) == str:
        databasePath = database
        # Ensure file exists
        if not os.path.isfile(databasePath):
            raise IOError("Database file does not exist.")

    elif type(database) == dict:
        databasePath = "database_" + startTime + ".fasta"
        writeFasta(databasePath, database)
    
    else:
        raise TypeError("database must be of type string or dict")

    outputPath = "output_" + startTime + ".txt"

    if alphabet == "nucleotide":
        dna_blast(queryPath, databasePath, outputPath, maxAccepts, maxRejects, minIdentity, strand)
    elif alphabet == "protein":
        protein_blast(queryPath, databasePath, outputPath, maxAccepts, maxRejects, minIdentity)

    csvPath = "output_" + strftime("%Y-%m-%d-%H:%M:%S", localtime()) + ".csv"
    writeCSV(outputPath, csvPath)

    # Delete query, database, and output files, if they were 
    # constructed in this function
    if type(query) == dict:
        os.remove(queryPath)
    if type(database) == dict:
        os.remove(databasePath)

    os.remove(outputPath)

    if outputToFile:
        return csvPath
    else:
        table = readCSV(csvPath)
        os.remove(csvPath)
        return table