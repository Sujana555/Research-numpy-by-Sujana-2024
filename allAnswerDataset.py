import csv

def readCsv(fileName):
    try:
        with open(fileName, mode='r', encoding='utf-8') as file:
            csvFile = csv.DictReader(file)
            return list(csvFile)
    except FileNotFoundError:
        raise FileNotFoundError(f"File, {fileName}, not found")
    except Exception as e:
        raise e

def getFavouriteCount(answerId, baseFileList):
    for row in baseFileList:
        if row['answerId'] == answerId:
            return row['favoriteCount']  # Ensure the key name matches the CSV file
    return 0  # Return 0 if no matching answerId is found

def getCommentCount(ansId, commentFile):
    commentList = readCsv(commentFile)
    commentCount = 0
    for row in commentList:
        if (row['answerId'] == ansId) and not row['commentId']:
            commentCount += 1
    return commentCount

def getCreationDate(answerId, baseFileList):
    for row in baseFileList:
        if row['answerId'] == answerId:
            return row['questionCreationDate']  # Ensure the key name matches the CSV file

def makingAnswerDataset(baseFileList, answerFile, commentFile):
    answerFileList = readCsv(answerFile)
    answerDataset = []
    for row in answerFileList:
        answerId = row['answerId']
        favoriteCount = getFavouriteCount(answerId, baseFileList)
        commentCount = getCommentCount(answerId, commentFile)
        creationDate = getCreationDate(answerId, baseFileList)
        tempDict = {
            'answerId': row['answerId'],
            'answerVoteCount': row['answerVotes'],
            'commentCount': commentCount,
            'favoriteCount': favoriteCount,
            'creationDate': creationDate
        }
        answerDataset.append(tempDict)
    return answerDataset

# Example usage:
baseFileList = readCsv('stackoverflow_questions.csv')
answerFile = 'answerList.csv'
commentFile = 'commentList.csv'
answerDataset = makingAnswerDataset(baseFileList, answerFile, commentFile)
print(answerDataset)
