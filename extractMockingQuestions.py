import requests
from bs4 import BeautifulSoup
import time
import logging
import csv
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_detailed_question_page(question_url):
    try:
        question_response = requests.get(question_url, headers={'User-agent': 'your bot 0.1'})
        question_response.raise_for_status()
        question_soup = BeautifulSoup(question_response.text, "html.parser")
        return question_soup
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to load page {question_url}: {e}")
        return None

def extract_question_comments(ques_comment_summaries):
    ques_comment_list = []
    for comment in ques_comment_summaries:
        comment_id = comment.get('data-comment-id')
        comment_owner = comment.select_one(".comment-user").get_text(strip=True)
        comment_score_element = comment.select_one(".comment-score")
        comment_score = comment_score_element.get_text(strip=True) if comment_score_element else 'N/A'
        comment_text = comment.select_one(".comment-copy").get_text(strip=True)
        temp_dict = {
            "comment_id": comment_id,
            "comment_owner": comment_owner,
            "comment_score": comment_score,
            "comment_text": comment_text
        }
        ques_comment_list.append(temp_dict)
    return ques_comment_list

def extract_answer_comments(comment_summaries):
    comment_list = []
    for comment in comment_summaries:
        comment_id = comment.get('data-comment-id')
        comment_owner = comment.select_one(".comment-user").get_text(strip=True)
        comment_score_element = comment.select_one(".comment-score")
        comment_score = comment_score_element.get_text(strip=True) if comment_score_element else 'N/A'
        comment_text = comment.select_one(".comment-copy").get_text(strip=True)
        comment_list.append({
            "comment_id": comment_id,
            "comment_owner": comment_owner,
            "comment_score": comment_score,
            "comment_text": comment_text
        })
    return comment_list

def get_answer_info(each_ques_summary):
    answer_summaries = each_ques_summary.select(".answer")
    answer_info_list = []
    answer_count_element = each_ques_summary.find(itemprop="answerCount")
    answer_count = answer_count_element.get_text(strip=True) if answer_count_element else "N/A"

    for answer in answer_summaries:
        answer_id = answer.get('data-answerid')
        answer_user_id_element = answer.select_one('.user-details a')
        answer_user_id = answer_user_id_element['href'].split('/')[-2] if answer_user_id_element else 'N/A'
        answer_body = answer.select_one(".s-prose").get_text(strip=True)
        answer_votes = answer.select_one(".js-vote-count").get_text(strip=True)
        answer_comments = extract_answer_comments(answer.select(".comment"))

        answer_info_list.append({
            "answerCount": answer_count,
            "answerId": answer_id,
            "answerUserId": answer_user_id,
            "answerBody": answer_body,
            "answerVotes": answer_votes,
            "comments": answer_comments
        })
    return answer_info_list

def storing_all_ques_info_together(ques_list, answer_info, ques_comments):
    ques_info_list = []
    answerCount = ""

    for answer in answer_info:
        base_dict = {
            "questionId": ques_list[0],
            "questionTitle": ques_list[1],
            "questionTags": ", ".join(ques_list[2]),
            "questionBody": ques_list[3],
            "questionVotes": ques_list[4],
            "questionViewCount": ques_list[5],
            "questionCreationDate": ques_list[6],
            "favoriteCount": ques_list[7],
            "answerCount": answer["answerCount"],
            "answerId": answer["answerId"],
            "answerUserId": answer["answerUserId"],
            "answerBody": answer["answerBody"],
            "answerVotes": answer["answerVotes"],
        }
        answerCount = answer["answerCount"]

        if not answer["comments"]:
            base_dict.update({
                "commentId": "",
                "commentOwner": "",
                "commentVotes": "",
                "commentText": ""
            })
            ques_info_list.append(base_dict)
        else:
            for comment in answer["comments"]:
                temp_dict = base_dict.copy()
                temp_dict.update({
                    "commentId": comment["comment_id"],
                    "commentOwner": comment["comment_owner"],
                    "commentVotes": comment["comment_score"],
                    "commentText": comment["comment_text"]
                })
                ques_info_list.append(temp_dict)


    for comment in ques_comments:
        ques_info_list.append({
            "questionId": ques_list[0],
            "questionTitle": ques_list[1],
            "questionTags": ", ".join(ques_list[2]),
            "questionBody": ques_list[3],
            "questionVotes": ques_list[4],
            "questionViewCount": ques_list[5],
            "questionCreationDate": ques_list[6],
            "favoriteCount": ques_list[7],
            "answerCount": answerCount,
            "answerId": "",
            "answerUserId": "",
            "answerBody": "",
            "answerVotes": "",
            "commentId": comment["comment_id"],
            "commentOwner": comment["comment_owner"],
            "commentVotes": comment["comment_score"],
            "commentText": comment["comment_text"]
        })

    print(ques_info_list)
    return ques_info_list

def get_question_info(ques_summary):
    ques_list = []
    ques_list.append(get_ques_id(ques_summary))
    ques_list.append(ques_summary.select_one(".s-link").get_text(strip=True))
    ques_list.append([tag.get_text(strip=True) for tag in ques_summary.select(".post-tag")])
    ques_list.append(ques_summary.select_one(".s-post-summary--content-excerpt").get_text(strip=True))
    ques_list.append(ques_summary.select_one(".s-post-summary--stats-item-number").get_text(strip=True))
    view_count_element = ques_summary.select_one(".is-supernova")
    ques_list.append(view_count_element.get("title") if view_count_element else "N/A")
    question_url = "https://stackoverflow.com" + ques_summary.select_one(".s-link")['href']

    each_ques_summary = get_detailed_question_page(question_url)
    if not each_ques_summary:
        logging.error(f"Failed to get detailed question page for {question_url}")
        return []

    ques_creation_date_element = each_ques_summary.find('time', itemprop='dateCreated')
    ques_list.append(ques_creation_date_element['datetime'] if ques_creation_date_element else "N/A")

    # Add favorite count
    favorite_count_element = each_ques_summary.select_one(".js-favorite-count")
    favorite_count = favorite_count_element.get_text(strip=True) if favorite_count_element else 0
    ques_list.append(favorite_count)

    answer_info_list = get_answer_info(each_ques_summary)  # getting the answers correctly

    ques_comment_summaries = each_ques_summary.select(".question .comment")
    ques_comment_list = extract_question_comments(ques_comment_summaries)

    question_info_list = storing_all_ques_info_together(ques_list, answer_info_list, ques_comment_list)
    return question_info_list

def get_ques_id(question_summary):
    question_url = question_summary.select_one(".s-link")['href']
    question_id = int(question_url.split('/')[2])
    return question_id





def save_to_csv(data, filename="stackoverflow_questions.csv"):
    if not data:
        print("Data list is empty. Nothing to write to CSV.")
        return

    file_exists = os.path.isfile(filename)
    keys = data[0].keys()  # Assuming data is not empty, get keys from the first dictionary

    retries = 5
    for attempt in range(retries):
        try:
            with open(filename, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=keys)
                if not file_exists:
                    writer.writeheader()  # Write header only if the file does not already exist
                for entry in data:
                    writer.writerow(entry)
            print(f"Data successfully saved to {filename}")
            return  # Exit the function after a successful write
        except PermissionError:
            print(f"Permission denied: Unable to write to '{filename}'. Attempt {attempt + 1} of {retries}. Retrying in 1 second...")
            time.sleep(30)  # Wait for a second before retrying
        except IOError as e:
            print(f"An I/O error occurred: {e}")
            return  # Exit the function on other I/O errors

    print(f"Failed to save data to '{filename}' after {retries} attempts.")

def scrape_stack_overflow_questions(base_url, max_questions, filename="stackoverflow_questions.csv"):
    page_num = 1
    all_question_info = []
    ques_summaries = []
    retries = 0
    max_retries = 5
    wait_time = 1  # initial wait time in seconds

    while len(ques_summaries) < max_questions:
        url = base_url + f"&page={page_num}"
        try:
            response = requests.get(url, headers={'User-agent': 'your bot 0.1'})
            response.raise_for_status()
            retries = 0  # reset retries on successful request
        except requests.exceptions.RequestException as e:
            if response.status_code == 429:  # Rate limited
                if 'Retry-After' in response.headers:
                    retry_after = int(response.headers['Retry-After'])
                    logging.info(f"Rate limited. Retrying after {retry_after} seconds...")
                    time.sleep(retry_after)
                else:
                    logging.warning("Rate limited but no Retry-After header. Waiting 15 seconds...")
                    time.sleep(15)
            else:
                retries += 1
                if retries >= max_retries:
                    logging.error(f"Failed to load page {url} after {max_retries} retries: {e}")
                    break
                wait_time *= 2  # exponential backoff
                logging.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        ques_summaries = soup.select(".s-post-summary.js-post-summary")

        if not ques_summaries:
            logging.info("No more questions found.")
            break

        for ques_summary in ques_summaries:
            if len(all_question_info) >= max_questions:
                break

            question_info_list = get_question_info(ques_summary)
            if question_info_list:
                save_to_csv(question_info_list, filename)
                all_question_info.extend(question_info_list)


        page_num += 1
        time.sleep(15)

    return all_question_info



# def save_to_csv(data, filename="stackoverflow_questions.csv"):
#     if not data:
#         logging.info("Data list is empty. Nothing to write to CSV.")
#         return
#
#     keys = data[0].keys()
#     with open(filename, mode='w', newline='', encoding='utf-8') as file:
#         writer = csv.DictWriter(file, fieldnames=keys)
#         writer.writeheader()
#         for entry in data:
#             writer.writerow(entry)
#     logging.info(f"Data successfully saved to {filename}")

# Usage
numpy_base_url = "https://stackoverflow.com/questions/tagged/mocking?tab=newest&page=10"
max_questions = 15000
questions_data = scrape_stack_overflow_questions(numpy_base_url, max_questions)

# Example of printing some of the data
for question in questions_data:
    print(question)


# import requests
# from bs4 import BeautifulSoup
# import time
# import random
# import logging
# import csv
#
# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
#
# def get_detailed_question_page(question_url):
#     try:
#         question_response = requests.get(question_url, headers = {'User-agent': 'your bot 0.1'})
#         question_response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
#         question_soup = BeautifulSoup(question_response.text, "html.parser")
#         return question_soup
#     except requests.exceptions.RequestException as e:
#         logging.error(f"Failed to load page {question_url}: {e}")
#         return None
#
#
#
# def extract_comment(comment_summaries):
#     comment_list = []
#     for comment in comment_summaries:
#         comment_id = comment.get('data-comment-id')
#         comment_owner = comment.select_one(".comment-user").get_text(strip=True)
#         comment_score = comment.select_one(".comment-score").get_text(strip=True)
#         comment_text = comment.select_one(".comment-copy").get_text(strip=True)
#
#         comment_list.append({
#             "comment_id": comment_id,
#             "comment_owner": comment_owner,
#             "comment_score": comment_score,
#             "comment_text": comment_text
#         })
#     return comment_list
#
#
# def get_answer_info(each_ques_summary):
#     answer_summaries = each_ques_summary.select(".answer")
#     answer_info_list = []
#     answerCount = each_ques_summary.find(itemprop="answerCount").getText()
#
#     for answer in answer_summaries:
#         answer_id = answer['data-answerid']
#         answer_user_id_element = answer.select_one('.user-details a')
#         answer_user_id = answer_user_id_element['href'].split('/')[-2] if answer_user_id_element else 'N/A'
#         answer_body = answer.select_one(".s-prose").get_text(strip=True)
#         answer_votes = answer.select_one(".js-vote-count").get_text(strip=True)
#         answer_comments = extract_comment(answer.select(".comment"))
#
#         # Combine answer info with each comment
#         for comment in answer_comments:
#             answer_info_list.append({
#                 "answerCount": answerCount,
#                 "answerId": answer_id,
#                 "answerUserId": answer_user_id,
#                 "answerBody": answer_body,
#                 "NoOfVotes": answer_votes,
#                 "comment_id": comment["comment_id"],
#                 "comment_owner": comment["comment_owner"],
#                 "comment_score": comment["comment_score"],
#                 "comment_text": comment["comment_text"]
#             })
#
#     return answer_info_list
#
#
# def get_question_info(ques_summary):
#     ques_id = get_ques_id(ques_summary)
#     ques_title = ques_summary.select_one(".s-link").getText()
#     ques_tags = [tag.getText() for tag in ques_summary.select(".post-tag")]
#     ques_body = ques_summary.select_one(".s-post-summary--content-excerpt").getText()
#     ques_votes = ques_summary.select_one(".s-post-summary--stats-item-number").getText()
#     view_count_element = ques_summary.select_one(".is-supernova")
#     question_view_count = view_count_element.get("title") if view_count_element else "N/A"
#     question_url = "https://stackoverflow.com" + ques_summary.select_one(".s-link")['href']
#
#     each_ques_summary = get_detailed_question_page(question_url)
#     if not each_ques_summary:
#         logging.error(f"Failed to get detailed question page for {question_url}")
#         return []
#     ques_creation_date_element = each_ques_summary.find('time', itemprop='dateCreated')
#     ques_creation_date = ques_creation_date_element['datetime'] if ques_creation_date_element else "N/A"
#
#     answer_info_list = get_answer_info(each_ques_summary)
#
#     question_info_list = []
#     for answer_info in answer_info_list:
#         for comment in answer_info["comments"]:
#             question_info_list.append({
#                 "questionId": ques_id,
#                 "questionTitle": ques_title,
#                 "questionTags": ", ".join(ques_tags),
#                 "questionBody": ques_body,
#                 "questionVotes": ques_votes,
#                 "questionViewCount": question_view_count,
#                 "questionCreationDate": ques_creation_date,
#                 "answerCount": answer_info["answerCount"],
#                 "answerId": answer_info["answerId"],
#                 "answerUserId": answer_info["answerUserId"],
#                 "answerBody": answer_info["answerBody"],
#                 "NoOfVotes": answer_info["NoOfVotes"],
#                 "comment_id": comment["comment_id"],
#                 "comment_owner": comment["comment_owner"],
#                 "comment_score": comment["comment_score"],
#                 "comment_text": comment["comment_text"]
#             })
#
#     return question_info_list
#
# def get_ques_id(question_summary):
#     question_url = question_summary.select_one(".s-link")['href']
#     question_id = int(question_url.split('/')[2])
#     return question_id
#
#
# def scrape_stack_overflow_questions(base_url, max_questions):
#     page_num = 1
#     all_question_info = []
#
#     while len(all_question_info) < max_questions:
#         url = base_url + f"&page={page_num}"
#         try:
#             response = requests.get(url, headers = {'User-agent': 'your bot 0.1'})
#             if response.status_code == 429:
#                 if 'Retry-After' in response.headers:
#                     retry_after = int(response.headers['Retry-After'])
#                     logging.info(f"Rate limited. Retrying after {retry_after} seconds...")
#                     time.sleep(retry_after)
#                     continue
#                 else:
#                     logging.warning("Rate limited but no Retry-After header. Waiting 5 seconds...")
#                     time.sleep(5)
#                     continue
#
#             response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
#         except requests.exceptions.RequestException as e:
#             logging.error(f"Failed to load page {url}: {e}")
#             break
#
#         soup = BeautifulSoup(response.text, "html.parser")
#         ques_summaries = soup.select(".s-post-summary.js-post-summary")
#
#         if not ques_summaries:
#             print("No more questions found.")
#             break
#
#         for ques_summary in ques_summaries:
#             question_info_list = get_question_info(ques_summary)
#             all_question_info.extend(question_info_list)
#
#             if len(all_question_info) >= max_questions:
#                 break
#
#         page_num += 1
#         time.sleep(60)
#
#     return all_question_info
#
# def save_to_csv(data, filename="stackoverflow_questions.csv"):
#     if not data:
#         print("Data list is empty. Nothing to write to CSV.")
#         return
#
#     keys = data[0].keys()  # Assuming data is not empty, get keys from the first dictionary
#     with open(filename, mode='w', newline='', encoding='utf-8') as file:
#         writer = csv.DictWriter(file, fieldnames=keys)
#         writer.writeheader()
#         for entry in data:
#             writer.writerow(entry)
#     print(f"Data successfully saved to {filename}")
#
# numpy_base_url = "https://stackoverflow.com/questions/tagged/numpy?tab=active&page=1"
# maxQuestions = 100
# questions_data = scrape_stack_overflow_questions(numpy_base_url, maxQuestions)
#
# # Save the scraped data to a CSV file
# save_to_csv(questions_data)
#
# # Example of printing some of the data
# for question in questions_data:
#     print(question)


