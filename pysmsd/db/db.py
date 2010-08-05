#
# pysmsd.db.db
#
# Copyright 2010 Helsinki Institute for Information Technology
# and the authors.
#
# Authors: Jani Turunen <jani.turunen@hiit.fi>
#          Konrad Markus <konrad.markus@hiit.fi>
#

# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from __future__ import with_statement

import logging
import sqlite3
import bcrypt

def is_authorized(db_path, name, password):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM `clients` WHERE `name`=?", (name,))
    row = c.fetchone()

    if row:
        if bcrypt.hashpw(password, row['password']) == row['password']:
            return row['id']

    return None

def mark_messages(db_path, client_id, id_list):
    seq = [(client_id, i) for i in id_list]
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executemany("UPDATE `in_messages` SET `marked_by`=?, `marked`=datetime('now'), `updated`=datetime('now') WHERE id=?", seq)
    conn.commit() 
    c.close()

def mark_message(db_path, client_id, id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("UPDATE `in_messages` SET `marked_by`=?, `marked`=datetime('now'), `updated`=datetime('now') WHERE id=?", (client_id, id))
    conn.commit() 
    c.close()

def insert_in_message(db_path, m):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("INSERT INTO `in_messages`(`number`, `text`, `length`, `coding`, `datetime`, `keyword`, `rest`, `created`, `updated`) VALUES(?,?,?,?,?,?,?, datetime('now'), datetime('now'))", (m['Number'], m['Text'], m['Length'], m['Coding'], m['Received'], m['Keyword'], m['Rest']))
    conn.commit() 
    rowid = c.lastrowid
    c.close()
    return rowid 

def get_in_message(db_path, id):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM `in_messages` WHERE `id`=?", (id,))
    return c.fetchone()

def get_in_messages(db_path, keyword=None, include_marked=False):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if keyword:
        if include_marked:
            c.execute("SELECT * FROM `in_messages` WHERE `keyword`=? ORDER BY `datetime`", (keyword,))
        else:
            c.execute("SELECT * FROM `in_messages` WHERE `keyword`=? AND `marked` IS NULL ORDER BY `datetime`", (keyword,))
    else:
        if include_marked:
            c.execute("SELECT * FROM `in_messages` ORDER BY `datetime`")
        else:
            c.execute("SELECT * FROM `in_messages` WHERE `marked` IS NULL ORDER BY `datetime`")
            
    return c

def insert_out_message(db_path, m, client_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("INSERT INTO `out_messages`(`number`, `text`, `length`, `queued_by`, `datetime`, `queued`, `sent`, `created`, `updated`) VALUES(?,?,?,?, datetime('now'), datetime('now'), datetime('now'), datetime('now'), datetime('now'))", (m['Number'], m['Text'], len(m['Text']), client_id))
    conn.commit() 
    rowid = c.lastrowid
    c.close()
    return rowid 

def get_out_message(db_path, id):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM `out_messages` WHERE `id`=?", (id,))
    return c.fetchone()

def get_out_messages(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM `out_messages` ORDER BY `datetime`")
    return c

