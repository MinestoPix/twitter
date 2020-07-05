import sqlite3

class Connection():

    def __init__(self):
        self.connection, self.cursor = self.get_connection_cursor()

    def close(self):
        self.connection.close()

    def get_connection_cursor(_):
        connection = sqlite3.connect('results.db')
        cursor = connection.cursor()
        return connection, cursor

    def enable_foreign_keys(self):
        enabled, = self.cursor.execute(
                "PRAGMA foreign_keys;"
                ).fetchone()
        if not enabled:
            self.cursor.execute("PRAGMA foreign_keys = ON;")
    
    def unique_users(_, res):
        users = []
        for result in res:
            users.append((result["user"]["handle"], result["user"]["name"]))
            if "mentions" in result:
                for mention in result["mentions"]:
                    users.append((mention["handle"], mention["name"]))

        return list(set(users))


    def insert_results(self, query, results):
        self.cursor.execute("""
                INSERT OR IGNORE INTO queries(query, result_count)
                VALUES (?, ?)
                """, (query, results["res_count"]))
        res = results["res"]

        users = self.unique_users(res)

        self.cursor.executemany("""
                INSERT OR IGNORE INTO users(handle, name)
                VALUES (?, ?)
                """, iter(users))
        for result in res:
            self.cursor.execute("""
                SELECT ROWID FROM queries WHERE query = ?
                """, (query,))
            result["query_id"], = self.cursor.fetchone()

            self.cursor.execute(
                    "SELECT ROWID FROM users WHERE handle = :handle",
                    result["user"])
            result["author_id"], = self.cursor.fetchone()

            self.cursor.execute("""
                INSERT INTO results(full_text, date, query, author)
                VALUES (:full_text, :when, :query_id, :author_id)
                """, result)

            result_id = self.cursor.lastrowid

            if "mentions" in result:
                for mention in result["mentions"]:
                    self.cursor.execute(
                    "SELECT ROWID FROM users WHERE handle = :handle",
                            mention)
                    author_id, = self.cursor.fetchone()
                    self.cursor.execute(
                    "INSERT INTO mentions(result, user) VALUES (?, ?)",
                        (result_id, author_id))

            if "hashtags" in result:
                for hashtag in result["hashtags"]:
                    self.cursor.execute(
                            "SELECT * FROM hashtags WHERE text = ?",
                            (hashtag["text"],))
                    existing_ht = self.cursor.fetchone()

                    if existing_ht:
                        self.cursor.execute("""
                                INSERT INTO hashtag_to_result(
                                    result, hashtag
                                ) VALUES (?, ?)
                                """, (result_id, existing_ht[0]))
                    else:
                        self.cursor.execute(
                                "INSERT INTO hashtags(text) VALUES (?)",
                                (hashtag["text"],))
                        self.cursor.execute("""
                                INSERT INTO hashtag_to_result(
                                    result, hashtag
                                ) VALUES (?, ?)
                                """, (result_id, self.cursor.lastrowid))
                        
        self.connection.commit()

    
    def get_query(self, query):
        self.cursor.execute(
                "SELECT * FROM queries WHERE query = ?",
                (query,))
        query = self.cursor.fetchone()

        if not query:
            return None

        query_id, query_txt, res_count = query

        json_dict = {
                "res_count":    res_count,
                "res_faces":    {},
                "res":          [],
                }

        self.cursor.execute(
                "SELECT * FROM results WHERE query = ?",
                (query_id,))
        for result in self.cursor.fetchall():
            result_dict = {}

            self.cursor.execute(
                    "SELECT * FROM hashtag_to_result WHERE result = ?",
                    (result[0],))
            hashtags = self.cursor.fetchall()
            if hashtags:
                hashtag_list = []
                for hashtag in hashtags:
                    self.cursor.execute(
                            "SELECT * FROM hashtags WHERE id = ?",
                            (hashtag[1],))
                    _, ht = self.cursor.fetchone()
                    hashtag_list.append({"text": ht})
                result_dict["hashtags"] = hashtag_list

            result_dict["full_text"] = result[1]

            self.cursor.execute(
                    "SELECT * FROM users WHERE id = ?",
                    (result[4],))
            _, handle, name = self.cursor.fetchone()
            self.cursor.execute(
                    "SELECT * FROM mentions WHERE result = ?",
                    (result[0],))
            mentions = self.cursor.fetchall()
            if mentions:
                mentions_list = []
                for mention in mentions:
                    self.cursor.execute(
                            "SELECT * FROM users WHERE id = ?",
                            (mention[1],))
                    user = self.cursor.fetchone()
                    mentions_list.append({
                        "name": user[2],
                        "handle": user[1],
                        })

                result_dict["mentions"] = mentions_list

            result_dict["user"] = {
                        "name":     name,
                        "handle":   handle,
                        }
            result_dict["when"] = result[2]

            json_dict["res"].append(result_dict)

        return json_dict
    
    def get_relations(self, user_handle):

        self.cursor.execute("""
            SELECT * FROM author_mentions WHERE (author = :handle
            OR mention = :handle) AND author != mention
            """, {'handle': user_handle})
        return self.cursor.fetchall()

    def get_relations_from_list(self, user_handles):
        exe_str = ["SELECT * FROM author_mentions WHERE (author != mention) "]

        exe_str.extend(f"AND (author IN ({','.join(['?'] * len(user_handles))}) ")
        exe_str.extend(f"OR mention IN ({','.join(['?'] * len(user_handles))}))")
        
        
        user_handles.extend(user_handles)

        # print(''.join(exe_str), user_handles)
        self.cursor.execute(''.join(exe_str), user_handles)
        return self.cursor.fetchall()


def init_tables(con, c):
    c.executescript("""
CREATE TABLE IF NOT EXISTS queries (
    id              INTEGER PRIMARY KEY,
    query           TEXT,
    result_count   INTEGER,
    UNIQUE (query)
);

CREATE TABLE IF NOT EXISTS users (
    id      INTEGER PRIMARY KEY,
    handle  TEXT,
    name    TEXT,
    UNIQUE (handle)
);

CREATE TABLE IF NOT EXISTS results (
    id          INTEGER PRIMARY KEY,
    full_text   TEXT,
    date        TEXT,
    query       INTEGER REFERENCES queries,
    author      INTEGER REFERENCES users
);
CREATE INDEX IF NOT EXISTS query_index ON results(query);
CREATE INDEX IF NOT EXISTS author_index ON results(author);

CREATE TABLE IF NOT EXISTS mentions (
    result      INTEGER REFERENCES results,
    user        INTEGER REFERENCES users,
    PRIMARY KEY(result, user)
);
CREATE INDEX IF NOT EXISTS result_index ON mentions(result);
CREATE INDEX IF NOT EXISTS user_index ON mentions(user);

CREATE TABLE IF NOT EXISTS hashtags (
    id      INTEGER PRIMARY KEY,
    text    TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS hashtag_to_result (
    result      INTEGER REFERENCES results,
    hashtag     INTEGER REFERENCES hashtags,
    PRIMARY KEY(result, hashtag)
);
CREATE INDEX IF NOT EXISTS result_index ON hashtag_to_result(result);
CREATE INDEX IF NOT EXISTS hashtag_index ON hashtag_to_result(hashtag);
    """)
    con.commit()



if __name__ == "__main__":
    connection = Connection()
    init_tables(connection.connection, connection.cursor)
    connection.close()
