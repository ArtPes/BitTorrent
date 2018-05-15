# coding=utf-8
import datetime
import re
import sys
from pymongo import MongoClient
from helpers.helpers import *
import math
import threading

class MongoConnection():

    def __init__(self, out_lck, host="localhost", port=27017, db_name='torrent', conn_type="local", username='',
                 password=''):
        self.out_lck = out_lck
        self.db_lck = threading.Lock()
        self.host = host
        self.port = port
        try:
            self.conn = MongoClient()
            self.db = self.conn[db_name]
            if "sessions" not in self.db.collection_names():
                self.db.create_collection("sessions")
            if "files" not in self.db.collection_names():
                self.db.create_collection("files")
            if "download" not in self.db.collection_names():
                self.db.create_collection("download")
            self.db.tracker.remove({})
            self.db.sessions.remove({})
        except Exception as e:
            output(self.out_lck, "Could not connect to server: " + str(e))

    def get_sessions(self):
        """
            Restituisce tutte le sessioni aperte
        """
        self.db_lck.acquire()
        try:
            cursor = self.db.sessions.find()
        except Exception as e:
            output(self.out_lck, "Database Error > get_sessions: " + str(e))
            self.db_lck.release()
        else:
            self.db_lck.release()
            return list(cursor)

    def get_session(self, session_id):
        self.db_lck.acquire()
        try:
            session = self.db.sessions.find_one({"session_id": session_id})
        except Exception as e:
            output(self.out_lck, "Database Error > get_session: " + str(e))
            self.db_lck.release()
        else:
            self.db_lck.release()
            return session

    def insert_session(self, ipv4, ipv6, port):
        """
            Inserisce una nuova sessione, o restitusce il session_id in caso esista già
        """
        self.db_lck.acquire()
        try:
            cursor = self.db.sessions.find_one({"ipv4": ipv4,
                                                "ipv6": ipv6,
                                                "port": port
                                                })
        except Exception as e:
            output(self.out_lck, "Database Error > insert_session: " + str(e))
            self.db_lck.release()
        else:
            if cursor is not None:
                output(self.out_lck, "User already logged in")
                self.db_lck.release()
                # Restituisco il session id esistente come da specifiche
                return cursor['session_id']
            else:
                try:
                    session_id = id_generator(16)
                    self.db.sessions.insert_one({"session_id": session_id,
                                                 "ipv4": ipv4,
                                                 "ipv6": ipv6,
                                                 "port": port
                                                 })
                    self.db_lck.release()
                    return session_id
                except Exception as e:
                    output(self.out_lck, "Database Error > insert_session: " + str(e))
                    self.db_lck.release()
                    return "0000000000000000"

    def remove_session(self, sessionID):
        self.db_lck.acquire()
        try:
            source = self.db.sessions.find_one({"session_id": sessionID})
            files = self.db.tracker.find({'peers.session_id': sessionID})
        except Exception as e:
            print("Database Error > remove_session: " + str(e))
            self.db_lck.release()
            return False
        if files is None:
            self.db.sessions.remove({'session_id': sessionID})
            self.db_lck.release()
            return True
        else:
            lista_file = list(files)
            for i in range(len(lista_file)):  # ciclo numero di file
                # estraggo la part_list del file i-esimo del utente che vuole fare logout
                myfile_list = self.db.tracker.find_one({'md5': lista_file[i]['md5']},
                                                     {'peers': {"$elemMatch": {'session_id': sessionID}},
                                                      '_id': 0})
                index2 = lista_file[i]
                # print index2['name']
                index_peer = index2['peers']
                n_parts = int(math.ceil(float(index2['len_file']) / float(index2['len_part'])))
                parts = []
                for j in range(0, n_parts - 1):  # ciclo parti del file
                    if myfile_list['peers'][0]['part_list'][j] == '1':  # controllo solo le parti che posseggo
                        # print myfile_list['peers'][0]['part_list'][j] mostro i mmiei bit
                        is_available = False
                        for peer in range(len(index_peer)):  # ciclo numero di peer
                            if index_peer[peer]['ipv4'] == source['ipv4']:
                                pass
                            else:
                                if index_peer[peer]['part_list'][j] == '1':
                                    # print index_peer[peer]['part_list'][j] + " : " + index_peer[peer]['ipv4'] + " " + str(j)
                                    is_available = True
                                    break
                                else:
                                    # print index_peer[peer]['part_list'][j] + " : " + index_peer[peer]['ipv4'] + " " + str(j)
                                    is_available = False
                        if is_available:
                            parts.append('1')  # parte presente
                        else:
                            parts.append('0')
                if '0' in parts:
                    self.db_lck.release()
                    # print "parti mancanti"
                    return False
                    break
                else:
                    # TODO: da provare
                    try:
                        print(lista_file[i]['md5'])
                        self.db.tracker.update({'md5': lista_file[i]['md5']},
                                             {"$pull": {'peers': {'session_id': sessionID}}})
                        pass
                    except Exception as e:
                        print("Database Error > update file in remuve_session: " + str(e))
                        self.db_lck.release()
                        return False
            self.db.sessions.remove({'session_id': sessionID})
            # TODO: eliminare sessione e part_list
            # db.getCollection('hitpeers').update({"md5": "md51"}, {'$pull': {"ipv4": { '$in': ["aaa"]}}})
            # db.tracker.update({'md5': md5}, {$unset: {'peers.$.part_list': 0}}) funziona 16-5
            # db.getCollection('hitpeers').update({'md5': "md51"}, {$pull: {'ipv4': {'a':"aa"}}})
            self.db_lck.release()
            return True

    def get_parts(self, md5):
        """
            Restituisce una lista di peer con ip+porta e la stringa delle parti possedute
        """
        # cursor = self.db.hitpeers.find({"md5": md5}, {"_id": 0, "md5": 0, "session_id": 0}) vecchia versione db
        # db.getCollection('hitpeers').find({md5: "md52"}, { _id : 0, md5 : 0, session_id : 0 })
        self.db_lck.acquire()
        try:
            cursor = self.db.tracker.find({"md5": md5},
                                        {"_id": 0, "md5": 0, "peers.session_id": 0, "name": 0, "len_part": 0,
                                         "len_file": 0})
        except Exception as e:
            output(self.out_lck, "Database Error > get_parts: " + str(e))
            self.db_lck.release()
        else:
            if cursor.count() > 0:
                # TODO: vedere lista
                peers = list(cursor)
                prova = peers[0]
                self.db_lck.release()
                return prova['peers']
            else:
                output(self.out_lck, "Database Error > get_parts: No parts found for " + md5)
                self.db_lck.release()

    def update_parts(self, md5, sessionID, n_part):
        # TODO: funziona ma migliorabile
        """
            seleziono con md5 e sessionID la parte da modificare, poi cambio il bit con indice n_part
        """
        self.db_lck.acquire()
        try:
            part = self.db.tracker.find_one({"md5": md5, "peers.session_id": sessionID})
        except Exception as e:
            output(self.out_lck, "Database Error > update_parts: " + str(e))
            self.db_lck.release()

        if part is not None:
            try:
                # self.db.tracker.update({'md5': md5, 'peers.session_id': sessionID}, {"$set": {'part_list': str_part}})
                # db.tracker.update({'md5': "3md5", 'peers.session_id': "id1"}, {"$set": {'part_list': "dddd"}}) funziona
                # db.getCollection('tracker').update({"md5": "1md5"}, {"$set": {"peers.part_list": "bbb"}})

                peer = self.db.tracker.find_one({'md5': md5, 'peers.session_id': sessionID},
                                              {'peers': {"$elemMatch": {'session_id': sessionID}}})
                # db.getCollection('tracker').findOne({'md5' : "3md5", 'peers.session_id' : "id1"}, {"peers": {"$elemMatch": {"session_id": "id1"}}})
                str_part_old = peer['peers'][0]['part_list']
                str_list = list(str_part_old)
                str_list[int(n_part)] = '1'
                str_part = "".join(str_list)

                self.db.tracker.update({"md5": md5, 'peers': {'$elemMatch': {'session_id': sessionID}}},
                                     {"$set": {'peers.$.part_list': str_part}})
                # db.getCollection('tracker').update({"md5": "1md5", 'peers': {'$elemMatch' : {'session_id':"id1"}}},{"$set":{'peers.$.part_list': "aaaaaaaaaa"}})
                self.db_lck.release()
            except Exception as e:
                output(self.out_lck, "Database Error > update_parts: " + str(e))
                self.db_lck.release()
        elif part is None:
            try:

                str_part = ""
                #part_list = ""
                session = self.db.sessions.find_one({"session_id": sessionID})
                peer = self.db.tracker.find_one({'md5': md5})
                LenFile = peer['len_file']
                LenPart = peer['len_part']
                n_parts = int(math.ceil(float(LenFile) / float(LenPart)))
                for i in range(0, n_parts):
                    if i == int(n_part):
                        str_part = "".join([str_part, '1'])
                    else:
                        str_part = "".join([str_part, '0'])
                #str_part[int(n_part)] = '1'
                #part_list = "".join(str_part)


                self.db.tracker.update({"md5": md5},
                                       {'$push': {'peers': {'port': session['port'], 'part_list': str_part,
                                                            'ipv4': session['ipv4'], 'session_id': sessionID,
                                                            'ipv6': session['ipv6']}}})
                # db.getCollection('hitpeers').update({'md5': 'md51'}, {'$push': {'ipv4': {'a': "aaaaa2", 'b': "bbbbbbb2"}}})
                self.db_lck.release()
            except Exception as e:
                output(self.out_lck, "Database Error > update_parts: " + str(e))
                self.db_lck.release()
        else:
            output(self.out_lck, "Database Error > update_parts: file " + md5 + " or user " + sessionID + " not found")
            self.db_lck.release()

    def insert_peer(self, name, md5, LenFile, LenPart, sessionID):
        self.db_lck.acquire()
        try:
            file = self.db.tracker.find_one({"md5": md5})
        except Exception as e:
            output(self.out_lck, "Database Error > insert_peer: " + str(e))
            self.db_lck.release()

        if file is None:
            # insert new file
            try:
                n_parts = int(math.ceil(float(LenFile) / float(LenPart)))
                str_part = ""
                for i in range(0, n_parts):
                    str_part = str_part + "1"

                peer = self.db.sessions.find_one({"session_id": sessionID})

                # TODO: sistemare database peer
                self.db.tracker.insert_one({"name": name, "md5": md5, "len_file": LenFile, "len_part": LenPart,
                                          'peers': [
                                              {'session_id': sessionID, 'ipv4': peer['ipv4'], 'ipv6': peer['ipv6'],
                                               'port': peer['port'], 'part_list': str_part}]})
                self.db_lck.release()
            except Exception as e:
                output(self.out_lck, "Database Error > insert_peer: " + str(e))
                self.db_lck.release()
        else:
            try:
                output(self.out_lck, "Database Error > insert_peer exist")
                # update new source
                n_parts = int(math.ceil(float(LenFile) / float(LenPart)))
                str_part = ""
                for i in range(0, n_parts):
                    str_part = str_part + "1"
                peer = self.db.sessions.find_one({"session_id": sessionID})
                self.db.tracker.update({'md5': md5}, {'$push': {'peers': {'session_id': sessionID, 'ipv4': peer['ipv4'],
                                                                       'ipv6': peer['ipv6'], 'port': peer['port'],
                                                                       'part_list': str_part}}})
                self.db_lck.release()
            except Exception as e:
                output(self.out_lck, "Database Error > insert_peer: " + str(e))
                self.db_lck.release()

    def get_files_tracker(self, query_str):
        """
            Restituisce i file il cui nome comprende la stringa query_str
        """
        self.db_lck.acquire()
        try:
            if query_str.strip(" ") == '*' or query_str.strip(" ") == '':
                files = self.db.tracker.find()
            else:
                regexp = re.compile(query_str.strip(" "), re.IGNORECASE)
                files = self.db.tracker.find({"name": {"$regex": regexp}})
            self.db_lck.release()
            return files
        except Exception as e:
            output(self.out_lck, "Database Error > get_files: " + str(e))
            self.db_lck.release()
        else:
            self.db_lck.release()
            return files

    def get_file_tracker(self, md5):
        self.db_lck.acquire()
        try:
            file = self.db.tracker.find_one({"md5": md5})
        except Exception as e:
            output(self.out_lck, "Database Error > get_file: " + str(e))
            self.db_lck.release()
        else:
            self.db_lck.release()
            return file

    def get_files(self, query_str):
        """
            Restituisce i file il cui nome comprende la stringa query_str
        """
        self.db_lck.acquire()
        try:
            if query_str.strip(" ") == '*' or query_str.strip(" ") == '':
                files = self.db.files.find()
            else:
                regexp = re.compile(query_str.strip(" "), re.IGNORECASE)
                files = self.db.files.find({"name": {"$regex": regexp}})
            self.db_lck.release()
            return files
        except Exception as e:
            output(self.out_lck, "Database Error > get_files: " + str(e))
            self.db_lck.release()
        else:
            self.db_lck.release()
            return files

    def get_file(self, md5):
        self.db_lck.acquire()
        try:
            file = self.db.files.find_one({"md5": md5})
        except Exception as e:
            output(self.out_lck, "Database Error > get_file: " + e)
            self.db_lck.release()
        else:
            self.db_lck.release()
            return file

    def insert_file(self, name, md5, len_file, len_part):
        self.db_lck.acquire()
        try:
            file = self.db.files.find_one({"md5": md5})
            if file is None:
                self.db.files.insert_one({"name": name,
                                            "md5": md5,
                                            "len_file": len_file,
                                            "len_part": len_part})
            else:
                self.db.files.update({"md5": md5}, {'$set': {"len_file": len_file, "len_part": len_part}})
        except Exception as e:
            output(self.out_lck, "Database Error > insert_file: " + e)
            self.db_lck.release()
        else:
            self.db_lck.release()

    def insert_file_tracker(self, name, md5, len_file, len_part):
        self.db_lck.acquire()
        try:
            file = self.db.tracker.find_one({"md5": md5})
            if file is None:
                self.db.tracker.insert_one({"name": name,
                                          "md5": md5,
                                          "len_file": len_file,
                                          "len_part": len_part})
            else:
                self.db.tracker.update({"md5": md5}, {'$set': {"len_file": len_file, "len_part": len_part}})
        except Exception as e:
            output(self.out_lck, "Database Error > insert_file_tracker: " + e)
            self.db_lck.release()
        else:
            self.db_lck.release()

    def get_download(self, md5):
        self.db_lck.acquire()
        try:
            download = self.db.download.find_one({"md5": md5})
        except Exception as e:
            output(self.out_lck, "Database Error > get_download: " + e)
            self.db_lck.release()
        else:
            self.db_lck.release()
            return download

    def insert_download(self, name, md5, len_file, len_part):
        parts = []
        self.db_lck.acquire()
        try:
            self.db.download.insert_one({
                "name": name,
                "md5": md5,
                "len_file": len_file,
                "len_part": len_part,
                "parts": parts
            })
        except Exception as e:
            output(self.out_lck, "Database Error > insert_download: " + e)
            self.db_lck.release()
        else:
            self.db_lck.release()

    def remove_download(self, md5):
        self.db_lck.acquire()
        try:
            self.db.download.remove({"md5": md5})
        except Exception as e:
            output(self.out_lck, "Database Error > remove_download: " + e)
            self.db_lck.release()
        else:
            self.db_lck.release()

    def update_download_parts(self, md5, sorted_parts):
        self.db_lck.acquire()
        try:
            self.db.download.update_one({"md5": md5},
                                        {
                                            "$set": {"parts": sorted_parts}
                                        })
        except Exception as e:
            output(self.out_lck, "Database Error > update_download_parts: " + e)
            self.db_lck.release()
        else:
            self.db_lck.release()

    def update_download(self, md5, part_n):
        self.db_lck.acquire()
        try:
            self.db.download.update(
                {"md5": md5, "parts": {"$elemMatch": {"n": part_n}}},
                {"$set": {"parts.$.downloaded": "true"}})
        except Exception as e:
            output(self.out_lck, "Database Error > update_download: " + e)
            self.db_lck.release()
        else:
            self.db_lck.release()

    def downloading(self, md5):
        self.db_lck.acquire()
        try:
            download = self.db.download.find_one({"md5": md5})
        except Exception as e:
            output(self.out_lck, "Database Error > downloading: " + e)
            self.db_lck.release()
        else:
            if download is not None:
                parts = download['parts']

                completed = True
                for part in parts:
                    if part['downloaded'] == "false":
                        completed = False
                self.db_lck.release()
                return completed
            else:
                output(self.out_lck, "Database Error > downloading: parts table not found for file " + md5)
                self.db_lck.release()
                return None

    def get_download_progress(self, md5):
        self.db_lck.acquire()
        try:
            download = self.db.download.find_one({"md5": md5})
        except Exception as e:
            output(self.out_lck, "Database Error > downloading: " + e)
            self.db_lck.release()
        else:
            if download is not None:
                parts = download['parts']
                parts_down = 0
                parts_tot = len(parts)

                for part in parts:
                    if part['downloaded'] == "true":
                        parts_down += 1

                self.db_lck.release()
                return parts_down, parts_tot
            else:
                output(self.out_lck, "Database Error > get_download_progress: parts table not found for file " + md5)
                self.db_lck.release()
                return None

    def get_downloadable_part(self, md5, idx):
        self.db_lck.acquire()
        try:
            cursor = self.db.download.find({"md5": md5}, {"parts": {"$elemMatch": {"n": idx}}})
            parts = list(cursor)
        except Exception as e:
            output(self.out_lck, "Database Error > get_downloadable_part: " + e)
            self.db_lck.release()
        else:
            if cursor.count() > 0:
                part = parts[0]['parts'][0]
                # part = parts['parts'][0]
                self.db_lck.release()
                return part
            else:
                output(self.out_lck, "Database Error > get_downloadable_part: part " + idx + " not found")
                self.db_lck.release()
                return None

    # partdown
    def get_number_partdown(self, sessionID):

        tot = 0
        self.db_lck.acquire()
        try:
            source = self.db.sessions.find_one({'session_id': sessionID})
            files = self.db.tracker.find({'peers.session_id': sessionID})
        except Exception as e:
            output(self.out_lck, "Database Error > get_number_partdown: " + e)
            self.db_lck.release()
        else:
            if files is None:
                self.db_lck.release()
                return 0
            else:
                lista_file = list(files)
                for i in range(len(lista_file)):  # ciclo numero di file
                    index2 = lista_file[i]
                    # print index2['name']
                    index_peer = index2['peers']
                    n_parts = int(math.ceil(float(index2['len_file']) / float(index2['len_part'])))
                    source_parts = self.db.tracker.find({'md5': index2['md5']},
                                                      {'peers': {"$elemMatch": {"session_id": sessionID}},
                                                       'peers.part_list': 1, '_id': 0})
                    source_bit = list(source_parts)[0]['peers'][0]['part_list']
                    parts = []
                    for j in range(0, len(source_bit)):  # ciclo paerti del file
                        is_available = False
                        if source_bit[j] == '1':
                            for peer in range(len(index_peer)):  # ciclo numero di peer
                                if index_peer[peer]['ipv4'] == source['ipv4']:
                                    pass
                                else:
                                    if index_peer[peer]['part_list'][j] == '1':
                                        # print index_peer[peer]['part_list'][j] + " : " + index_peer[peer][
                                        #     'ipv4'] + " indice: " + str(j)
                                        is_available = True
                                        break
                                    else:
                                        # print index_peer[peer]['part_list'][j] + " : " + index_peer[peer][
                                        #     'ipv4'] + " indicie: " + str(j)
                                        is_available = False
                            if is_available:
                                parts.append('1')  # parte presente
                            else:
                                parts.append('0')
                        else:
                            pass
                    tot += parts.count('1')

                self.db_lck.release()
                return tot

    # partown tutte le parti a 1 sul db
    def get_number_partown(self, sessionID):
        tot = 0
        self.db_lck.acquire()
        try:
            source = self.db.sessions.find_one({'session_id': sessionID})
            files = self.db.tracker.find({'peers.session_id': sessionID})
        except Exception as e:
            output(self.out_lck, "Database Error > get_number_partdown: " + e)
            self.db_lck.release()
        else:
            if files is None:
                self.db_lck.release()
                return 0
            else:
                lista_file = list(files)
                for i in range(len(lista_file)):  # ciclo numero di file
                    index2 = lista_file[i]
                    index_peer = index2['peers']
                    n_parts = int(math.ceil(float(index2['len_file']) / float(index2['len_part'])))
                    source_parts = self.db.tracker.find({'md5': index2['md5']},
                                                      {'peers': {"$elemMatch": {"session_id": sessionID}},
                                                       'peers.part_list': 1, '_id': 0})
                    source_bit = list(source_parts)[0]['peers'][0]['part_list']
                    parts = []
                    for j in range(0, len(source_bit)):  # ciclo parti del file
                        if source_bit[j] == '1':
                            parts.append('1')
                            pass
                        else:
                            parts.append('0')
                            pass
                    tot += parts.count('1')
                self.db_lck.release()
                return tot

    def number_part(self,sessionID):
        tot = 0
        self.db_lck.acquire()
        try:
            source = self.db.sessions.find_one({'session_id': sessionID})
            files = self.db.tracker.find({'peers.session_id': sessionID})
        except Exception as e:
            output(self.out_lck, "Database Error > get_number_partdown: " + e)
            self.db_lck.release()
        if files is None:
            self.db_lck.release()
            return 0
        else:
            lista_file = list(files)
            for i in range(len(lista_file)):
                index2 = lista_file[i]
                #index_peer = index2['peers']
                tot += int(math.ceil(float(index2['len_file']) / float(index2['len_part'])))
            self.db_lck.release()
            return tot

    def new_remove_session(self, sessionID):
        self.db_lck.acquire()
        tot_part_down = 0
        tot_part_own = 0
        logout = True
        try:
            source = self.db.sessions.find_one({"session_id": sessionID})
            files = self.db.tracker.find({'peers.session_id': sessionID})
        except Exception as e:
            print("Database Error > remove_session: " + e)
            self.db_lck.release()
            return False
        if files is None:
            self.db.sessions.remove({'session_id': sessionID})
            self.db_lck.release()
            return "T" + '000000000'
        else:
            lista_file = list(files)
            for i in range(len(lista_file)):  # ciclo numero di file
                # estraggo la part_list del file i-esimo del utente che vuole fare logout
                my_file_list = self.db.tracker.find_one({'md5': lista_file[i]['md5']},
                                                      {'peers': {"$elemMatch": {'session_id': sessionID}}, '_id': 0})
                index_peer = lista_file[i]['peers']  # lista dei peer del file
                n_parts = int(math.ceil(float(lista_file[i]['len_file']) / float(lista_file[i]['len_part'])))
                parts_own = []
                parts_down = []
                for j in range(0, n_parts - 1):  # ciclo parti del file
                    is_available = False
                    if my_file_list['peers'][0]['part_list'][j] == '1':  # controllo solo le parti che posseggo
                        parts_own.append('1')
                        for peer in range(len(index_peer)):  # ciclo numero di peer
                            if index_peer[peer]['ipv4'] == source['ipv4']:
                                pass
                            else:
                                if index_peer[peer]['part_list'][j] == '1':
                                    is_available = True
                                    break
                                else:
                                    is_available = False
                        if is_available:
                            parts_down.append('1')  # parte presente
                        else:
                            parts_down.append('0')
                tot_part_down += parts_down.count('1')
                tot_part_own += parts_own.count('1')
                if '0' in parts_down:
                    logout = False
            if logout and (tot_part_down == tot_part_own):
                for i in range(len(lista_file)):
                    self.db.tracker.update({'md5': lista_file[i]['md5']}, {"$pull": {'peers': {'session_id': sessionID}}})
                self.db.sessions.remove({'session_id': sessionID})
                self.db_lck.release()
                return "T" + str(tot_part_own).zfill(10)
            else:
                self.db_lck.release()
                return "F" + str(tot_part_down).zfill(10)

    def refresh(self):
        self.db.download.drop()
        self.db.files.drop()
        self.db.session.drop()
        self.db.tracker.drop()