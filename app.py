#!/usr/keio/Anaconda3-2023.09-0/bin/python

import sqlite3
from typing import Final, Optional, Union
import unicodedata

from flask import Flask, g, redirect, render_template, request, url_for, flash
from werkzeug import Response

# データベースのファイル名
DATABASE: Final[str] = 'report3.db'

# Flask クラスのインスタンス
app = Flask(__name__)

def get_db() -> sqlite3.Connection:
    """
    データベース接続を得る.

    リクエスト処理中にデータベース接続が必要になったら呼ぶ関数。

    Flask の g にデータベース接続が保存されていたらその接続を返す。
    そうでなければデータベース接続して g に保存しつつ接続を返す。
    その際に、カラム名でフィールドにアクセスできるように設定変更する。

    https://flask.palletsprojects.com/en/3.0.x/patterns/sqlite3/
    のサンプルにある関数を流用し設定変更を追加。

    Returns:
      sqlite3.connect: データベース接続
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.execute('PRAGMA foreign_keys = ON')  # 外部キー制約を有効化
        db.row_factory = sqlite3.Row  # カラム名でアクセスできるよう設定変更
    return db


@app.teardown_appcontext
def close_connection(exception: Optional[BaseException]) -> None:
    """
    データベース接続を閉じる.

    リクエスト処理の終了時に Flask が自動的に呼ぶ関数。

    Flask の g にデータベース接続が保存されていたら閉じる。

    https://flask.palletsprojects.com/en/3.0.x/patterns/sqlite3/
    のサンプルにある関数をそのまま流用。

    Args:
      exception (Optional[BaseException]): 未処理の例外
    """
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def has_control_character(s: str) -> bool:
    """
    文字列に制御文字が含まれているか否か判定する.

    Args:
      s (str): 判定対象文字列
    Returns:
      bool: 含まれていれば True 含まれていなければ False
    """
    return any(map(lambda c: unicodedata.category(c) == 'Cc', s))


@app.route('/')
def index():
    db = get_db()
    # データベース内容を取得
    query = "SELECT movies.id, movies.title, movies.release_year, movies.genre, movies.rating, directors.name AS director_name FROM movies LEFT JOIN directors ON movies.director_id = directors.id"
    movies = db.execute(query).fetchall()
    # 視聴履歴の内容を取得
    
    # 映画ジャンルの一覧を取得
    genre_query = "SELECT DISTINCT genre FROM movies ORDER BY genre ASC"
    genres = db.execute(genre_query).fetchall()
    db.close()
    return render_template('index.html', movies=movies, genres=genres)

@app.route('/genre/<string:genre>')
def genre_movies(genre):
    db = get_db()
    # 指定ジャンルの映画を取得
    query = """
        SELECT movies.id, movies.title, movies.release_year, movies.genre, movies.rating,
               directors.name AS director_name
        FROM movies
        LEFT JOIN directors ON movies.director_id = directors.id
        WHERE movies.genre = ?
    """
    movies = db.execute(query, (genre,)).fetchall()
    return render_template('genre.html', genre=genre, movies=movies)

@app.route('/filter', methods=['GET', 'POST'])
def filter_movies():
    conn = get_db()
    genre = request.args.get('genre', '')
    director = request.args.get('director', '')
    query = """SELECT movies.id, movies.title, movies.release_year, movies.genre, movies.rating, directors.name AS director_name
               FROM movies
               LEFT JOIN directors ON movies.director_id = directors.id
               WHERE movies.genre LIKE ? AND directors.name LIKE ?"""
    movies = conn.execute(query, (f"%{genre}%", f"%{director}%")).fetchall()
    conn.close()
    return render_template('index.html', movies=movies)

if __name__ == '__main__':
    # このスクリプトを直接実行したらデバッグ用 Web サーバで起動する
    app.run(debug=True)
