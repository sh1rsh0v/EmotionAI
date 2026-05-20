import requests
import pandas as pd
import random
import time
import os
from collections import defaultdict
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('esports_collector.log'),
        logging.StreamHandler()
    ]
)

FILE_NAME = "esports_tweets.csv"

API_KEY = ""
BASE_URL = "https://api.twitterapi.io/twitter/tweet/advanced_search"
HEADERS = {"X-API-Key": API_KEY}

TARGET_TWEETS = 10000
CHECKPOINT_EVERY = 100
NEUTRAL_RATIO = 0.8

# Фильтр по дате: строго 2025 год
DATE_FILTER = "since:2024-01-01_00:00:00_UTC until:2024-12-31_23:59:59_UTC"

# ---------- COMPLETE ESPORTS NEUTRAL QUERIES ----------

ESPORT_NEUTRAL_QUERIES = {
    "cs2": [
        # Турниры и организации
        "cs2", "counter strike 2", "counter-strike 2", "csgo", "cs:go",
        "blast premier", "iem", "esl pro league", "pgl major", 
        "blast world final", "major championship", "dreamhack",
        # Команды
        "navi", "faze clan", "team vitality", "g2 esports", "astralis",
        "virtus.pro", "mouz", "nip", "cloud9", "fnatic",
        "team liquid", "evil geniuses", "heroic", "ence",
        # Игроки
        "s1mple", "zywoo", "device", "niko", "electronic",
        "ropz", "kennys", "coldzera", "fallen", "get_right", "olofmeister",
        # Специфичные CS термины
        "de_dust2", "mirage", "inferno", "nuke", "overpass", "vertigo", "ancient",
        "awp", "defuse", "plant",
        # Хэштеги
        "#cs2", "#counterstrike", "#csgo", "#blastpremier", "#iem"
    ],

    "dota2": [
        # Турниры
        "dota2", "dota 2", "the international", "ti14",
        "dota pro circuit", "dreamleague", "pgl", "esl one", "riyadh masters",
        # Команды  
        "team spirit", "og", "team liquid", "evil geniuses", "psg.lgd",
        "team secret", "virtus.pro", "natus vincere", "tundra esports",
        "t1", "fnatic", "cloud9", "alliance",
        # Игроки
        "miracle", "topson", "n0tail", "kuroky", "sumail",
        "rtz", "ana", "ceb", "gh", "mind_control", "collapse", "yatoro",
        # Уникальные Dota термины
        "roshan", "ancient", "bkb",
        "radiance", "blink dagger",
        # Хэштеги
        "#dota2", "#theinternational", "#ti14"
    ],

    "lol": [
        # Турниры и лиги
        "league of legends", "wild rift", "lol wild rift", "lol esports", "lolesports", 
        "lck", "lcs", "lec", "lpl",
        # Команды
        "t1", "g2 esports", "fnatic", "cloud9", "team liquid", 
        "100 thieves", "evil geniuses", "gen.g", "kt rolster", 
        "dwg kia", "edward gaming", "rng", "top esports", "jd gaming",
        # Игроки
        "faker", "deft", "rekkles", "doublelift",
        "bjergsen", "theshy", "knight", "chovy",
        # Уникальные LoL термины
        "baron", "rift herald", "nexus", "inhibitor",
        "pentakill",
        # Хэштеги
        "#lol", "#leagueoflegends", "#lolesports", "#wildrift", "#worlds2025"
    ],

    "valorant": [
        # Турниры
        "valorant", "valorant esports", "valesports", 
        "vct", "valorant champions", "champions tour", "masters",
        # Команды
        "sentinels", "100 thieves", "optic", "navi", "fnatic",
        "team liquid", "paper rex", "drx", "edward gaming",
        "cloud9", "g2 esports",
        # Игроки
        "tenz", "scream", "yay", "derke", "ardiis", "sacy",
        "pancada", "marved", "fns", "boaster", "suygetsu",
        # Уникальные Valorant термины
        "jett", "raze", "reyna", "sova", "sage", "omen",
        "killjoy",
        # Хэштеги
        "#valorant", "#vct", "#valesports", "#valorantchampions"
    ]
}


# ---------- COMPLETE EMOTION QUERIES ----------

EMOTION_QUERIES = {
    "joy": [
        "insane play", "amazing play", "unbelievable play", "incredible play",
        "what a play", "holy shit play", "godlike", "phenomenal", "brilliant play",
        "masterpiece", "epic win", "historic win", "dominant victory", "stomped",
        "reverse sweep", "comeback", "against all odds", "hype moment", "pog moment",
        "lets go", "proud", "gg wp", "well played", "clean play", "perfect game",
        "flawless", "dominant", "outplayed", "skill gap", "career highlight",
        "play of tournament", "best play ever", "record breaking", "historic performance"
    ],

    "anger": [
        "throw game", "choke", "bad call", "terrible decision", "awful play",
        "disaster", "embarrassing", "unacceptable", "rage", "fuming", "pissed off",
        "bullshit", "rigged", "cheater", "hacker", "fix", "script", "boosted",
        "worst play", "horrible", "disgrace", "shameful", "pathetic", "useless",
        "garbage", "trash", "brain dead", "idiot", "moron", "noob", "boosted animal",
        "should be banned", "report", "ff", "surrender", "uninstall"
    ],

    "sadness": [
        "heartbreaking loss", "devastating loss", "brutal loss", "painful loss",
        "so close", "almost had it", "unlucky", "tough loss", "sad ending",
        "emotional loss", "gut wrenching", "soul crushing", "depressing",
        "disappointing", "let down", "what could have been",
        "missed opportunity", "hard to watch", "pain", "suffering", "hopeless",
        "end of era", "retirement", "last game", "final match", "goodbye"
    ],

    "surprise": [
        "unbelievable comeback", "shocking upset", "astonishing", "mind blowing",
        "absolutely insane", "did that just happen", "no way", "wtf just happened",
        "unexpected", "out of nowhere", "shock win", "huge upset", "underdog win",
        "miracle", "impossible", "can't believe", "speechless", "jaw dropping",
        "earth shattering", "game changing", "turning point", "plot twist"
    ],

    "fear": [
        "clutch moment", "tense moment", "heart pounding", "edge of seat",
        "nail biter", "down to wire", "last second", "final moment", "pressure",
        "high stakes", "do or die", "elimination game", "match point", "game point",
        "anxious", "nervous", "scared", "terrifying", "heart attack", "stress",
        "intense", "critical moment", "decisive moment", "clutch or kick",
        "save or die", "last hope", "final stand"
    ],

    "disgust": [
        "controversial", "disputed", "questionable", "debate", "argument",
        "should have", "robbery", "cheated", "unfair", "biased", "rigged",
        "disgraceful", "shame", "pitiful", "laughable", "joke", "clown fiesta",
        "mess", "dumpster fire", "train wreck", "car crash", "painful to watch",
        "cringe", "awkward", "embarrassing", "sham", "farce", "mockery"
    ],

    "neutral": [
        "analysis", "breakdown", "review", "recap", "summary", "highlights",
        "stats", "statistics", "numbers", "data", "explanation", "educational",
        "learning", "tutorial", "guide",
        "strategy", "tactical", "composition", "draft", "pick ban",
        "meta", "metagame", "patch", "update", "changes", "balance"
    ]
}


class BalancedEsportsCollector:
    def __init__(self):
        self.tweets = []
        self.seen_ids = set()
        self.game_counts = defaultdict(int)
        self.emotion_counts = defaultdict(int)
        self.last_checkpoint_count = 0
        self.batch_stats = {
            'total_neutral': 0,
            'total_emotional': 0,
            'current_batch_neutral': 0,
            'current_batch_emotional': 0
        }

        # Список всех игр для round-robin
        self.game_list = list(ESPORT_NEUTRAL_QUERIES.keys())
        self.game_index = 0  # Текущий индекс в round-robin

        if os.path.exists(FILE_NAME):
            self.load_existing_data()

    def load_existing_data(self):
        try:
            df_existing = pd.read_csv(FILE_NAME)
            self.tweets = df_existing.to_dict("records")
            self.seen_ids = set(df_existing["id"].astype(str))

            for tweet in self.tweets:
                self.game_counts[tweet["game"]] += 1
                if tweet.get("query_type") == "emotional":
                    self.emotion_counts[tweet.get("target_emotion", "neutral")] += 1
                    self.batch_stats['total_emotional'] += 1
                else:
                    self.batch_stats['total_neutral'] += 1

            self.last_checkpoint_count = len(self.tweets)
            logging.info(f"Resumed with {len(self.tweets)} tweets")
            logging.info(f"Games: {dict(self.game_counts)}")
            logging.info(f"Emotions: {dict(self.emotion_counts)}")

        except Exception as e:
            logging.error(f"Error loading existing data: {e}")
            self.tweets = []
            self.seen_ids = set()

    # ---------- API REQUEST ----------

    def fetch_batch(self, query, cursor=""):
        params = {
            "query": f"{query} lang:en -is:retweet {DATE_FILTER}",
            "queryType": "Latest"
        }

        if cursor:
            params["cursor"] = cursor

        try:
            response = requests.get(
                BASE_URL, headers=HEADERS, params=params, timeout=15
            )

            if response.status_code == 401:
                logging.error("API Key Unauthorized")
                return [], ""
            elif response.status_code == 429:
                #logging.warning("Rate limit. Waiting 60 seconds...")
                time.sleep(5)
                return [], ""
            elif response.status_code != 200:
                logging.error(f"Status {response.status_code}: {response.text}")
                return [], ""

            data = response.json()

            if data.get("status") == "error":
                logging.error(f"API Error: {data.get('message')}")
                return [], ""

            tweets = data.get("tweets", [])
            has_next = data.get("has_next_page", False)
            next_cursor = data.get("next_cursor", "") if has_next else ""

            return tweets, next_cursor

        except requests.exceptions.Timeout:
            logging.warning("Request timed out")
            return [], ""
        except Exception as e:
            logging.error(f"Request error: {e}")
            return [], ""

    # ---------- ROUND-ROBIN GAME SELECTION ----------

    def select_game_round_robin(self):
        """Строго равномерный выбор игр по кругу"""
        game = self.game_list[self.game_index]
        self.game_index = (self.game_index + 1) % len(self.game_list)
        return game

    # ---------- BALANCE LOGIC ----------

    def get_batch_requirements(self, batch_size):
        neutral_needed = int(batch_size * NEUTRAL_RATIO)
        emotion_needed = batch_size - neutral_needed
        return neutral_needed, emotion_needed

    def choose_query_strategy(self, neutral_needed, emotion_needed):
        cn = self.batch_stats['current_batch_neutral']
        ce = self.batch_stats['current_batch_emotional']

        if cn < neutral_needed and ce >= emotion_needed:
            return "neutral"
        elif ce < emotion_needed and cn >= neutral_needed:
            return "emotional"
        else:
            nr = cn / max(neutral_needed, 1)
            er = ce / max(emotion_needed, 1)
            return "neutral" if nr < er else "emotional"

    def select_emotion(self):
        if not self.emotion_counts:
            return random.choice(list(EMOTION_QUERIES.keys()))

        min_count = min(self.emotion_counts.values())
        underrepresented = [
            e for e, c in self.emotion_counts.items() if c <= min_count + 5
        ]
        return random.choice(
            underrepresented if underrepresented
            else list(EMOTION_QUERIES.keys())
        )

    def construct_query(self, query_type, game, emotion):
        if query_type == "neutral":
            query = random.choice(ESPORT_NEUTRAL_QUERIES[game])
            return query, "neutral"
        else:
            emotion_query = random.choice(EMOTION_QUERIES[emotion])
            if game == "general_esports":
                query = emotion_query
            else:
                query = f"{game} {emotion_query}"
            return query, emotion

    # ---------- TWEET PROCESSING ----------

    def process_tweet(self, tweet, game, emotion, query_type):
        tweet_id = str(tweet.get("id", ""))

        if not tweet_id or tweet_id in self.seen_ids:
            return False

        text = tweet.get("text", "")
        if len(text) < 10:
            return False

        self.seen_ids.add(tweet_id)

        new_tweet = {
            "id": tweet_id,
            "text": text,
            "date": tweet.get("createdAt", ""),
            "lang": tweet.get("lang", ""),
            "game": game,
            "query_type": query_type,
            "target_emotion": emotion,
            "retweet_count": tweet.get("retweetCount", 0),
            "reply_count": tweet.get("replyCount", 0),
            "like_count": tweet.get("likeCount", 0),
            "quote_count": tweet.get("quoteCount", 0),
            "view_count": tweet.get("viewCount", 0),
            "bookmark_count": tweet.get("bookmarkCount", 0),
            "is_reply": tweet.get("isReply", False),
            "source": tweet.get("source", ""),
            "author_username": tweet.get("author", {}).get("userName", ""),
            "author_name": tweet.get("author", {}).get("name", ""),
            "author_followers": tweet.get("author", {}).get("followers", 0)
        }

        self.tweets.append(new_tweet)
        self.game_counts[game] += 1
        self.emotion_counts[emotion] += 1

        if query_type == "neutral":
            self.batch_stats['total_neutral'] += 1
            self.batch_stats['current_batch_neutral'] += 1
        else:
            self.batch_stats['total_emotional'] += 1
            self.batch_stats['current_batch_emotional'] += 1

        return True

    # ---------- CHECKPOINT ----------

    def save_checkpoint(self):
        try:
            df = pd.DataFrame(self.tweets)
            df.to_csv(FILE_NAME, index=False)
            self.last_checkpoint_count = len(self.tweets)
            self.batch_stats['current_batch_neutral'] = 0
            self.batch_stats['current_batch_emotional'] = 0

            logging.info(
                f"Checkpoint: {len(self.tweets)} tweets | "
                f"N:{self.batch_stats['total_neutral']} "
                f"E:{self.batch_stats['total_emotional']} | "
                f"Games: {dict(self.game_counts)}"
            )
        except Exception as e:
            logging.error(f"Error saving: {e}")

    # ---------- MAIN COLLECTION LOOP ----------

    def collect(self):
        logging.info(
            f"Target: {TARGET_TWEETS} | "
            f"Ratio: {NEUTRAL_RATIO*100}%N / {(1-NEUTRAL_RATIO)*100}%E | "
            f"Checkpoint: {CHECKPOINT_EVERY} | "
            f"Date: 2025 only"
        )

        while len(self.tweets) < TARGET_TWEETS:
            try:
                tweets_since = len(self.tweets) - self.last_checkpoint_count
                remaining = CHECKPOINT_EVERY - tweets_since
                batch_size = min(remaining, TARGET_TWEETS - len(self.tweets))

                if batch_size <= 0:
                    self.save_checkpoint()
                    continue

                neutral_needed, emotion_needed = self.get_batch_requirements(batch_size)
                batch_collected = 0

                while batch_collected < batch_size and len(self.tweets) < TARGET_TWEETS:

                    # Round-robin выбор игры
                    game = self.select_game_round_robin()

                    # Выбор типа запроса для баланса 80/20
                    query_type = self.choose_query_strategy(
                        neutral_needed, emotion_needed
                    )
                    emotion = (
                        self.select_emotion() if query_type == "emotional"
                        else "neutral"
                    )
                    query, actual_emotion = self.construct_query(
                        query_type, game, emotion
                    )

                    logging.info(
                        f"Searching: '{query}' | {game} | {query_type} | {actual_emotion}"
                    )

                    # Первая страница
                    tweets_batch, next_cursor = self.fetch_batch(query)

                    if not tweets_batch:
                        time.sleep(1)
                        continue

                    # Обработка первой страницы
                    for tweet in tweets_batch:
                        if batch_collected >= batch_size:
                            break
                        if self.process_tweet(
                            tweet, game, actual_emotion, query_type
                        ):
                            batch_collected += 1

                    # Пагинация
                    while (
                        next_cursor
                        and batch_collected < batch_size
                        and len(self.tweets) < TARGET_TWEETS
                    ):
                        time.sleep(0.5)
                        tweets_batch, next_cursor = self.fetch_batch(
                            query, next_cursor
                        )

                        if not tweets_batch:
                            break

                        for tweet in tweets_batch:
                            if batch_collected >= batch_size:
                                break
                            if self.process_tweet(
                                tweet, game, actual_emotion, query_type
                            ):
                                batch_collected += 1

                    logging.info(
                        f"Batch: {batch_collected}/{batch_size} | "
                        f"Total: {len(self.tweets)}/{TARGET_TWEETS}"
                    )

                    time.sleep(5)

                if len(self.tweets) - self.last_checkpoint_count >= CHECKPOINT_EVERY:
                    self.save_checkpoint()

            except Exception as e:
                logging.error(f"Error: {e}")
                time.sleep(5)

        self.save_checkpoint()
        logging.info("Done!")

        df = pd.DataFrame(self.tweets)
        logging.info(f"\n===FINAL===:\n"
                     f"Total: {len(df)}\n"
                     f"Games:\n{df['game'].value_counts()}\n"
                     f"Emotions:\n{df['target_emotion'].value_counts()}\n"
                     f"Types:\n{df['query_type'].value_counts()}")


def main():
    collector = BalancedEsportsCollector()
    try:
        collector.collect()
    except KeyboardInterrupt:
        logging.info("Interrupted. Saving...")
        collector.save_checkpoint()
    except Exception as e:
        logging.error(f"Fatal: {e}")
        collector.save_checkpoint()


if __name__ == "__main__":
    main()
