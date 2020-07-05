import requests
import time
import json
import sys
import database as db



def get_result_dict_and_save(query):
    connection = db.Connection()
    result = connection.get_query(query)
    if result:
        return result

    result = requests.get(LINK + "?query=" + query)
    result.raise_for_status()
    result_dict = json.loads(result.text)
    connection.insert_results(query, result_dict)
    return result_dict

def get_results_recurse_users(queries, iter_num, iter_max):
    results = []
    for query in queries:
        results.extend(get_result_dict_and_save(query)["res"])

    if iter_num >= iter_max:
        return results
    else:
        users = []
        for result in results:
            users.append(result["user"]["handle"])
            if "mentions" in result:
                for mention in result["mentions"]:
                    users.append(mention["handle"])

        return get_results_recurse_users(list(set(users)), iter_num + 1, iter_max)



def pretty_tweet(tweet):
    print(tweet["user"]["name"])
    print("@" + tweet["user"]["handle"])
    print()
    print(tweet["full_text"])
    if "mentions" in tweet:
        print()
        for mention in tweet["mentions"]:
            print("@" + mention["handle"])

def main():
    time_app = time.time()
    res_num = 0
    if len(sys.argv) == 1:
        print("""
USAGE: python main.py QUERY [NUMBER]

QUERY       string to query from database if stored, else api
NUMBER      NUMBERth result, default 0, negative for all (shorthand -)
            """)
        return
    if len(sys.argv) > 1:
        query = sys.argv[1]
    if len(sys.argv) > 2:
        if sys.argv[2][0] == "-":
            res_num = -1
        else:
            res_num = int(sys.argv[2])

    try:
        result_dict = get_result_dict_and_save(query)
        res = result_dict["res"]
    except requests.exceptions.ConnectionError as e:
        print(e)
        print()
        print("No offline results availible for query '" + query + "'\n")
        res = []

    print(time.time() - time_app)
    if len(res) > 0:
        max_res = len(res) - 1
        if res_num >= 0:
            if res_num > max_res:
                print(res_num, "too big, displaying result no.", max_res)
            pretty_tweet(res[min(res_num, max_res)])
        else:
            for tweet in res:
                pretty_tweet(tweet)
                print("--------------------------------------------")
    else:
        print("No Results")
    print(time.time() - time_app)

if __name__ == "__main__":
    main()
