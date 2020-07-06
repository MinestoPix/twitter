import requests
import time
import json
import sys
import database as db



def get_result_dict_and_save(query):
    with db.Connection() as connection:
        result = connection.get_query(query)
        if result:
            return result

    global LINK
    if not "LINK" in globals():
        try:
            with open("link.txt", "r") as l_txt:
                LINK = l_txt.read()
        except Exception as e:
            if "-l" in sys.argv:
                with open("link.txt", "w") as l_txt:
                    LINK = sys.argv[sys.argv.index("-l") + 1]
                    l_txt.write(LINK)
                    del sys.argv[sys.argv.index("-l") + 1]
                    del sys.argv[sys.argv.index("-l")]
            else:
                print(e)
                print()
                print("""
I need a link to work with. \
Enter it with 'twitter -l LINK', \
or write it to link.txt in directory of execution.
                """)
                sys.exit(1)

    result = requests.get(LINK + "?query=" + query)
    result.raise_for_status()
    result_dict = json.loads(result.text)

    with db.Connection() as connection:
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

        return get_results_recurse_users(list(set(users)),
                iter_num + 1, iter_max)


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
    if len(sys.argv) == 1:
        print("""
USAGE: python main.py QUERY [NUMBER]

QUERY       string to query from database if stored, else api
NUMBER      NUMBERth result, default 0, negative for all (shorthand -)
            """)
        return
    args = sys.argv.copy()
    if "-l" in args:
        del args[args.index("-l") + 1]
        del args[args.index("-l")]
    if len(args) > 1:
        query = args[1]
    if len(args) > 2:
        if args[2][0] == "-":
            res_num = -1
        else:
            res_num = int(args[2])
    else:
        res_num = 0

    try:
        result_dict = get_result_dict_and_save(query)
        res = result_dict["res"]
    except requests.exceptions.ConnectionError as e:
        print(e)
        print()
        print("No offline results availible for query '" + query + "'\n")
        res = []

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

if __name__ == "__main__":
    main()
