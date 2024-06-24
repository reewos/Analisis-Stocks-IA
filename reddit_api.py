import praw
import json
from datetime import datetime  
from collections import Counter

#Variables

from util import *

def connect_reddit():
    try: 
        reddit = praw.Reddit(
            client_id = os.getenv['REDDIT_CLIENT_ID'], 
            client_secret = os.getenv['REDDIT_CLIENT_SECRET'], 
            user_agent = os.getenv['REDDIT_USER_AGENT'] 
        )
    except Exception as e:
        print("Error: ", e)
    
    return reddit

def get_lastest_submission_comments_by_subreddits(subreddits,submission_count,comment_count=None):
    
    reddit = connect_reddit()

    dict_subreddits = {}
    dict_submissions = {}
    
    for subreddit in subreddits:
        for submission in reddit.subreddit(subreddit).new(limit=submission_count):
            submission.comments.replace_more(limit=0)
            list_of_comments = []
            if comment_count is not None:
                for comment in submission.comments[:comment_count]:
                    list_of_comments.append({
                        'id':comment.id,
                        'author':comment.author.name,
                        'score':comment.score,
                        'created_utc':str(datetime.fromtimestamp(comment.created_utc)),
                        'body':comment.body.strip()})
            else:
                for comment in submission.comments:
                    list_of_comments.append({
                        'id':comment.id,
                        'author':comment.author.name,
                        'score':comment.score,
                        'created_utc':str(datetime.fromtimestamp(comment.created_utc)),
                        'body':comment.body.strip()})
            
            dict_submissions[submission.id] = {
                'title': submission.title,
                'num_comments': submission.num_comments,
                'upvote_ratio': submission.upvote_ratio,
                'created_utc':str(datetime.fromtimestamp(submission.created_utc)),
                'comments': list_of_comments}
        dict_subreddits[subreddit] = dict_submissions
    
    return json.dumps(dict_subreddits)

def get_lastest_comments_by_subreddits(subreddits,limit=100):
    reddit = connect_reddit()
    
    dict_subreddits = {}
    for sr in subreddits:
        subreddit = reddit.subreddit(sr)
        comments = []
        for comment in subreddit.comments(limit=limit):
            dict_comment = {'id':comment.id,
                            'parent_id':comment.parent_id,
                            'author':comment.author.name,
                            'score':comment.score,
                            'created_utc':str(datetime.fromtimestamp(comment.created_utc)),
                            'body':comment.body.strip()}
            comments.append(dict_comment)
        dict_subreddits[sr] = comments
    return json.dumps(dict_subreddits)

# get_subreddits_comments(['stocks'],['APPL'],3,3)