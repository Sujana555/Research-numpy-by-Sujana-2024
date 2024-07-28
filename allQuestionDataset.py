import csv

def read_csv(file_name):  # will receive the base file
    """Read a CSV file and return a list of dictionaries."""
    try:
        with open(file_name, mode='r', encoding='utf-8') as file:
            csv_file = csv.DictReader(file)
            return list(csv_file)
    except FileNotFoundError:
        raise FileNotFoundError(f"File '{file_name}' not found.")
    except Exception as e:
        raise e

def get_ques_comment_count(ques_id, comment_list):
    """Return the count of comments for a given question ID."""
    comment_count = 0
    for row in comment_list:
        if (row['questionId'] == ques_id) and (row['answerId'] == ''):
            comment_count += 1
    return comment_count

def make_ques_dataset(base_list, comment_list):
    """Create a dataset of questions with their respective comment counts."""
    question_dataset = []

    for row in base_list:
        ques_id = row['questionId']
        ques_comment_count = get_ques_comment_count(ques_id, comment_list)
        temp_dict = {
            'questionId': row['questionId'],
            'quesViewCount': row['questionViewCount'],
            'answerCount': row['answerCount'],
            'quesCommentCount': ques_comment_count,
            'favouriteCount': row['favouriteCount']
        }
        question_dataset.append(temp_dict)

    return question_dataset

baseList = read_csv("stackoverflow_questions.csv")
commentList = read_csv("commentList.csv")

questionDataset = make_ques_dataset(baseList, commentList)
