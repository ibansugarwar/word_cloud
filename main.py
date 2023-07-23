import re
import time
import requests
import pandas as pd

from bs4 import BeautifulSoup

def get_tables(url, page):
    response = requests.get(f"{url}0/{page}/")
    # lxmlはパーサー
    soup = BeautifulSoup(response.text, 'lxml')
    # ページ内の全テーブルを取得
    tables = soup.find_all('table')
    return tables

def get_song_list(url):

    # 保存するDataFrameのカラム名
    columns_names = ['曲名', '歌手名', '作詞者名', '作曲者名', '歌い出し', '歌詞URL']

    all_song_list = []
    page_no = 0

    # ページ毎のループ
    while True:
        page_no += 1
        # ページ単位でのテーブルを取得する。
        tables = get_tables(url, page_no)

        # テーブルが取得できない場合は終了
        if len(tables) == 0:
            break

        # 1秒間スリープ（負荷対策）
        time.sleep(1)

        # テーブル毎のループ
        for table in tables:
            for row in table.find_all('tr', class_='border-bottom'):
                row_data = []

                # ヘッダー以外の行の場合に処理を実行する。
                if row.find('td') is not None:

                    # 「曲名」〜「歌い出し」までのカラムを追加
                    song_name = row.find_all('span')[0].text
                    artist = row.find_all('td')[1].text
                    lyricist = row.find_all('td')[2].text
                    composer = row.find_all('td')[3].text
                    start_singing = row.find_all('span')[3].text
                    song_url = row.find('a', class_='py-2 py-lg-0').get('href')

                    # 行を追加
                    row_data.append(song_name)
                    row_data.append(artist)
                    row_data.append(lyricist)
                    row_data.append(composer)
                    row_data.append(start_singing)
                    row_data.append(song_url)

                    all_song_list.append(row_data)

    # データフレームに格納して返す
    lyrics_df = pd.DataFrame(all_song_list, columns=columns_names)

    return lyrics_df

lylics_url = "https://www.uta-net.com/artist/22653/"
lyrics_df = get_song_list(lylics_url)

def get_lyrics(lyrics_url, url_count, comp_count=[0]):
    comp_count[0] += 1
    print(str(comp_count[0]) + '/' + str(url_count) + '曲 歌詞URL：' + lyrics_url)

    # 歌詞URL
    url = f"https://www.uta-net.com{lyrics_url}"
    # 歌詞取得
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    song_lyrics = soup.find('div', id='kashi_area')
    lyrics = song_lyrics.text
    # 1秒間スリープ（負荷対策）
    time.sleep(1)
    return lyrics

lyrics_df["歌詞"] = lyrics_df["歌詞URL"].apply(get_lyrics, url_count = len(lyrics_df))
lyrics_df.to_csv('scraped.csv')
print('スクレイピング 完了')




from wordcloud import WordCloud
import MeCab
import collections

mecab = MeCab.Tagger("-Owakati")

def text_to_words(text):
    words_song = []
    # 分解した単語ごとにループする。
    node = mecab.parseToNode(text)
    while node:
        word_type = node.feature.split(",")[0]
        # 名詞、形容詞、副詞、動詞の場合のみ対象
        if word_type in ["名詞", "形容詞", "副詞", "動詞"]:

        # ひらがな、１文字、「っ」で終わる単語　は対象外
            pattern = re.compile(r'[あ-ん]+')
            if not (pattern.fullmatch(node.surface) or len(node.surface) <= 1):
                if not (node.surface[-1] == 'っ'):
                    words_song.append(node.surface)

        node = node.next

    # 曲毎の単語の重複を削除して'空白区切のテキストを返す。
    words = ' '.join(set(words_song))
    return words

lyrics_df["words"] = lyrics_df["歌詞"].apply(text_to_words)
print('形態素解析 完了')

# 全曲の単語を結合する。
words_all = ' '.join(lyrics_df['words'].tolist())
lyrics_df.to_csv('scraped.csv')

# 出現頻度を表示
word_list = words_all.split(' ')
c = collections.Counter(word_list)
most_count_list = c.most_common()
columns_name = ['種類', '出現頻度']
print('【出現頻度 上位10個】----------------------')
print(pd.DataFrame(most_count_list, columns=columns_name)[:10])

# 除去する単語がある場合は指定
stop_words = ['そう', 'ない', 'いる', 'する', 'まま', 'よう',
              'てる', 'なる', 'こと', 'もう', 'いい', 'ある',
              'ゆく', 'れる', 'なっ', 'ちゃっ', 'ちょっ',
              'ちょっ', 'やっ', 'あっ', 'ちゃう', 'その', 'あの',
              'この', 'どの', 'それ', 'あれ', 'これ', 'どれ',
              'から', 'なら', 'だけ', 'じゃあ', 'られ', 'たら', 'のに',
              'って', 'られ', 'ずっ', 'じゃ', 'ちゃ', 'くれ', 'なんて', 'だろ',
              'でしょ', 'せる', 'なれ', 'どう', 'たい', 'けど', 'でも', 'って',
              'まで', 'なく', 'もの', 'ここ', 'どこ', 'そこ', 'さえ', 'なく',
              'たり', 'なり', 'だっ', 'まで', 'ため', 'ながら', 'より', 'られる', 'です']

# wordCloud生成
wordcloud = WordCloud(background_color="white",
                      font_path="/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
                      width=800,
                      height=400,
                      collocations=False,
                      stopwords=set(stop_words)).generate(words_all)

# ワードアートを保存
wordcloud.to_file("ward_art.png")
