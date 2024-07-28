import csv

def readCsvFile(fileName):
    try:
        with open(fileName, mode='r') as file:
            csvFile = csv.DictReader(file)
            return list(csvFile)
    except FileNotFoundError:
        raise FileNotFoundError(f"File {fileName} not found.")
    except Exception as e:
        raise e
def storeQuestions(baseFile):
    # make a list for the question file
    questionsList = []
    seenQuestionsIds = set()
    for row in baseFile:
        if row['questionId'] not in seenQuestionsIds:
            questionsList.append({
                'questionId': row['questionId'],
                'questionTitle': row['questionTitle'],
                'questionTags': row['questionTags'],
                'questionBody': row['questionBody'],
                'questionVotes': row['questionVotes'],
                'questionViewCount': row['questionViewCount'],
                'questionCreationDate': row['questionCreationDate'],
                "favoriteCount": row["favoriteCount"],
                'answerCount': row['answerCount']
            })
            seenQuestionsIds.add(row['questionId'])

    return questionsList

def storeAnswers(baseFile):
    seenAnswerIds = set()
    answerList = []

    for row in baseFile:
        if row["answerId"]:
            if row['answerId'] not in seenAnswerIds:
                seenAnswerIds.add(row['answerId'])
                answerList.append({
                    'questionId': row['questionId'],
                    'answerCount': row['answerCount'],
                    'answerId': row['answerId'],
                    'answerUserId': row['answerUserId'],
                    'answerBody': row['answerBody'],
                    'answerVotes': row['answerVotes']
                })
    return answerList

def storeComments(baseFile):
    seenCommentIds = set()
    commentList = []

    for row in baseFile:
        if row["commentId"]:
            if row['commentId'] not in seenCommentIds:
                seenCommentIds.add(row['commentId'])
                commentList.append({
                    'questionId': row['questionId'],
                    'answerId': row['answerId'],
                    'commentId': row['commentId'],
                    'commentOwner': row['commentOwner'],
                    'commentVotes': row['commentVotes'],
                    'commentText': row['commentText']
                })
    return commentList

def saveDataToCsv(data, filename):
    if not data:
        print("Data list is empty. Nothing to write to CSV.")
        return

    keys = data[0].keys()  # Assuming data is not empty, get keys from the first dictionary
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        for entry in data:
            writer.writerow(entry)
    print(f"Data successfully saved to {filename}")



baseFile = readCsvFile("stackoverflow_questions.csv")
questionList = storeQuestions(baseFile)
answerList = storeAnswers(baseFile)
commentList = storeComments(baseFile)

saveDataToCsv(questionList, "questionList.csv")
saveDataToCsv(answerList, "answerList.csv")
saveDataToCsv(commentList, "commentList.csv")