import requests
from bs4 import BeautifulSoup
import time
import logging
import csv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_detailed_question_page(question_url):
    try:
        question_response = requests.get(question_url, headers={'User-agent': 'your bot 0.1'})
        question_response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        question_soup = BeautifulSoup(question_response.text, "html.parser")
        return question_soup
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to load page {question_url}: {e}")
        return None

def extract_comment(comment_summaries, each_question_summaries):
    comment_list = []
    seenQuesCommentUser = set()
    comments = each_question_summaries.select(".comment-text.js-comment-text-and-form")
    for comment in comments:
        comment_id = comment.get('data-comment-id')
        comment_owner = comment.select_one(".comment-user").get_text(strip=True)
        comment_score_element = comment.select_one(".comment-score")
        comment_score = comment_score_element.get_text(strip=True) if comment_score_element else 'N/A'
        comment_text = comment.select_one(".comment-copy").get_text(strip=True)
        tempDict = {
            "comment_id": comment_id,
            "comment_owner": comment_owner,
            "comment_score": comment_score,
            "comment_text": comment_text

        }
        comment_list.append(tempDict)
        seenQuesCommentUser.add(comment_owner)

    for comment in comment_summaries:
        comment_id = comment.get('data-comment-id')
        comment_owner = comment.select_one(".comment-user").get_text(strip=True)
        comment_score = comment.select_one(".comment-score").get_text(strip=True)
        comment_text = comment.select_one(".comment-copy").get_text(strip=True)

        comment_list.append({
            "comment_id": comment_id,
            "comment_owner": comment_owner,
            "comment_score": comment_score,
            "comment_text": comment_text
        })
    return comment_list, seenQuesCommentUser

def get_answer_info(each_ques_summary):
    answer_summaries = each_ques_summary.select(".answer")
    answer_info_list = []
    answer_count_element = each_ques_summary.find(itemprop="answerCount")
    answer_count = answer_count_element.get_text(strip=True) if answer_count_element else "N/A"
    seenComments = set( )


    for answer in answer_summaries:
        answer_id = answer['data-answerid']
        answer_user_id_element = answer.select_one('.user-details a')
        answer_user_id = answer_user_id_element['href'].split('/')[-2] if answer_user_id_element else 'N/A'
        answer_body = answer.select_one(".s-prose").get_text(strip=True)
        answer_votes = answer.select_one(".js-vote-count").get_text(strip=True)
        answer_comments, seenComments = extract_comment(answer.select(".comment"), each_ques_summary)

        answer_info_list.append({
            "answerCount": answer_count,
            "answerId": answer_id,
            "answerUserId": answer_user_id,
            "answerBody": answer_body,
            "answerVotes": answer_votes,
            "comments": answer_comments
        })

    return answer_info_list, seenComments


def storingAllQuesInfoTogether(quesList, answerInfo, seenComments):
    quesInfoList = []

    for answer_info in answerInfo:
        # Base dictionary to store common information
        baseDict_one = {
            "questionId": quesList[0],
            "questionTitle": quesList[1],
            "questionTags": ", ".join(quesList[2]),
            "questionBody": quesList[3],
            "questionVotes": quesList[4],
            "questionViewCount": quesList[5],
            "questionCreationDate": quesList[6],
            "answerCount": answer_info["answerCount"],
            "answerId": answer_info["answerId"],
            "answerUserId": answer_info["answerUserId"],
            "answerBody": answer_info["answerBody"],
            "answerVotes": answer_info["answerVotes"],
        }
        baseDict_two = {
            "questionId": quesList[0],
            "questionTitle": quesList[1],
            "questionTags": ", ".join(quesList[2]),
            "questionBody": quesList[3],
            "questionVotes": quesList[4],
            "questionViewCount": quesList[5],
            "questionCreationDate": quesList[6],
            "answerCount": answer_info["answerCount"]
        }

        if not answer_info["comments"]:
            # If there are no comments, add default values
            baseDict_one.update({
                "commentId": "N/A",
                "commentOwner": "N/A",
                "commentVotes": "N/A",
                "commentText": "N/A"
            })
            quesInfoList.append(baseDict_one)
        else:
            # If there are comments, create a new entry for each comment
            for comment in answer_info["comments"]:
                if comment['commentOwner'] in seenComments:  # this will have the question comment when answer infos are null
                    tempDict = baseDict_two.copy()
                    tempDict.update({
                        "answerId": answer_info["answerId"],
                        "answerUserId": answer_info["answerUserId"],
                        "answerBody": answer_info["answerBody"],
                        "answerVotes": answer_info["answerVotes"],
                        "commentId": comment["comment_id"],
                        "commentOwner": comment["comment_owner"],
                        "commentVotes": comment["comment_score"],
                        "commentText": comment["comment_text"]
                    })
                    quesInfoList.append(tempDict)
                else:
                    tempDict = baseDict_one.copy()  # Create a copy of the baseDict
                    tempDict.update({
                        "commentId": comment["comment_id"],
                        "commentOwner": comment["comment_owner"],
                        "commentVotes": comment["comment_score"],
                        "commentText": comment["comment_text"]
                    })
                    quesInfoList.append(tempDict) # Consider moving this to outside the loop for clarity


    return quesInfoList


def get_question_info(ques_summary):
    quesList = []

    quesList.append(get_ques_id(ques_summary))
    quesList.append(ques_summary.select_one(".s-link").get_text(strip=True))
    quesList.append([tag.get_text(strip=True) for tag in ques_summary.select(".post-tag")])
    quesList.append(ques_summary.select_one(".s-post-summary--content-excerpt").get_text(strip=True))
    quesList.append(ques_summary.select_one(".s-post-summary--stats-item-number").get_text(strip=True))
    view_count_element = ques_summary.select_one(".is-supernova")
    quesList.append(view_count_element.get("title") if view_count_element else "N/A")
    question_url = "https://stackoverflow.com" + ques_summary.select_one(".s-link")['href']

    each_ques_summary = get_detailed_question_page(question_url)
    if not each_ques_summary:
        logging.error(f"Failed to get detailed question page for {question_url}")
        return []

    #comments
    # comments = each_ques_summary.select(".comment-text .comment-copy")
    # quesComments = [comment.get_text(strip=True) for comment in comments]
    # for comment in quesComments:
    #     print(quesList[0], comment)
    quesList.append(ques_summary)  # the item quesList[6] contains the question comment list
    ques_creation_date_element = each_ques_summary.find('time', itemprop='dateCreated')
    quesList.append(ques_creation_date_element['datetime'] if ques_creation_date_element else "N/A")

    answer_info_list, seenComments = get_answer_info(each_ques_summary)
    # print(answer_info_list)

    question_info_list = storingAllQuesInfoTogether(quesList, answer_info_list, seenComments)

    # for item in question_info_list:
    #     print(item)
    return question_info_list



def get_ques_id(question_summary):
    question_url = question_summary.select_one(".s-link")['href']
    question_id = int(question_url.split('/')[2])
    return question_id

def scrape_stack_overflow_questions(base_url, max_questions):
    page_num = 1
    all_question_info = []

    while len(all_question_info) < max_questions:
        url = base_url + f"&page={page_num}"
        try:
            response = requests.get(url, headers={'User-agent': 'your bot 0.1'})
            if response.status_code == 429:
                if 'Retry-After' in response.headers:
                    retry_after = int(response.headers['Retry-After'])
                    logging.info(f"Rate limited. Retrying after {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                else:
                    logging.warning("Rate limited but no Retry-After header. Waiting 5 seconds...")
                    time.sleep(5)
                    continue

            response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to load page {url}: {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        ques_summaries = soup.select(".s-post-summary.js-post-summary")

        if not ques_summaries:
            print("No more questions found.")
            break

        for ques_summary in ques_summaries:
            question_info_list = get_question_info(ques_summary)
            all_question_info.extend(question_info_list)

            if len(all_question_info) >= max_questions:
                break

        page_num += 1
        time.sleep(10)

    return all_question_info

def save_to_csv(data, filename="stackoverflow_questions.csv"):
    quesNumber = 0
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

numpy_base_url = "https://stackoverflow.com/questions/tagged/numpy?tab=active&page=1"
max_questions = 2
questions_data = scrape_stack_overflow_questions(numpy_base_url, max_questions)

# Save the scraped data to a CSV file
save_to_csv(questions_data)

# Example of printing some of the data
# for question in questions_data:
#     print(question)


