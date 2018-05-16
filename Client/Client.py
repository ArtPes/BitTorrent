# coding=utf-8
import math
import time

from bitarray import bitarray

from .SharedFile import SharedFile
from helpers import connection
from helpers.scheduler import Scheduler
from helpers.helpers import *
import threading, json, collections
from multiprocessing import Pool
from .DownloadingThreadPool import ThreadPool
from bitstring import BitArray

import binascii



class Client(object):

    session_id = None
    files_list = []
    path = "./fileCondivisi"
    tracker = None
    parallel_downloads = 5
    part_size = 262144
    pool = None

    def __init__(self, my_ipv4, my_ipv6, my_port, track_ipv4, track_ipv6, track_port, database, out_lck, print_trigger, download_trigger, download_progress_trigger):
        """
            Costruttore della classe Peer
        """

        self.my_ipv4 = my_ipv4
        self.my_ipv6 = my_ipv6
        self.my_port = my_port
        self.track_ipv4 = track_ipv4
        self.track_ipv6 = track_ipv6
        self.track_port = track_port
        self.dbConnect = database
        self.out_lck = out_lck
        self.json_lck = threading.Lock()
        self.procedure_lck = threading.Lock()
        self.print_trigger = print_trigger
        self.download_trigger = download_trigger
        self.download_progress_trigger = download_progress_trigger
        self.fetch_scheduler = None
        self.fetching = False

        # Searching for shareable files
        for root, dirs, files in os.walk(self.path):
            for file in files:
                file_md5 = hashfile(open(self.path+"/" + file, 'rb'), hashlib.md5())
                new_file = SharedFile(file, file_md5)
                self.files_list.append(new_file)

    def login(self):
        # IPP2P:RND <> IPT:3000
        # > “LOGI”[4B].IPP2P[55B].PP2P[5B]
        # < “ALGI”[4B].SessionID[16B]

        self.procedure_lck.acquire()

        # “LOGI”[4B].IPP2P[55B].PP2P[5B]
        output(self.out_lck, "Logging in...")

        msg = 'LOGI' + self.my_ipv4 + '|' + self.my_ipv6 + str(self.my_port).zfill(5)
        response_message = None
        try:
            self.tracker = None
            c = connection.Connection(self.track_ipv4, self.track_ipv6, self.track_port, self.print_trigger, "0")  # Creazione connessione con la directory
            c.connect()
            self.tracker = c.socket

            self.tracker.send(msg.encode('utf-8'))  # mando il messaggio di richiesta di login

            # stampo nella grafica
            self.print_trigger.emit(
                '=> ' + str(self.tracker.getpeername()[0]) + '  ' + msg[0:4] + '  ' + self.my_ipv4 + '  ' +
                self.my_ipv6 + '  ' + str(self.my_port).zfill(5), "00")
            self.print_trigger.emit("", "00")  # Space

            response_message = recvall(self.tracker, 20).decode('ascii')  # Risposta della directory, deve contenere ALGI e il session id
            # stampo nella grafica la risposta
            self.print_trigger.emit(
                '<= ' + str(self.tracker.getpeername()[0]) + '  ' + response_message[0:4] + '  ' + response_message[4:20],
                '02')
            self.print_trigger.emit("", "00")  # Space

        except Exception as e:
            self.print_trigger.emit('Error: ' + str(e), '01')
            self.print_trigger.emit("", "00")  # Space

        if response_message is None:
            output(self.out_lck, 'No response from tracker. Login failed')
            self.procedure_lck.release()
        else:
            self.session_id = response_message[4:20]
            if self.session_id == '0000000000000000' or self.session_id == '':
                output(self.out_lck, 'Troubles with the login procedure.\nPlease, try again.')
            else:
                output(self.out_lck, 'Session ID assigned by the directory: ' + self.session_id)
                output(self.out_lck, 'Login completed')

            self.procedure_lck.release()

    def logout(self):
        # IPP2P:RND <> IPT:3000
        # > “LOGO”[4B].SessionID[16B]
        # 1 < “NLOG”[4B].  # partdown[10B]
        # 2 < “ALOG”[4B].  # partown[10B]

        self.procedure_lck.acquire()

        output(self.out_lck, 'Logging out...')
        msg = 'LOGO' + self.session_id

        response_message = None
        try:
            self.check_connection()

            self.tracker.send(msg.encode('utf-8'))  # richiesta di logout

            self.print_trigger.emit('=> ' + str(self.tracker.getpeername()[0]) + '  ' + msg[0:4] + '  ' + self.session_id,
                                    "00")
            self.print_trigger.emit("", "00")  # Space

            response_message = recvall(self.tracker, 14).decode('ascii')
            n_parts = response_message[4:14]
            tot_parts = self.dbConnect.number_part(self.session_id)

            self.print_trigger.emit(
                '<= ' + str(self.tracker.getpeername()[0]) + '  ' + response_message[0:4] + '  ' + n_parts,
                '02')
            self.print_trigger.emit("", "00")  # Space

        except Exception as e:
            self.print_trigger.emit('Error: ' + str(e), '01')
            self.print_trigger.emit("", "00")  # Space

        if response_message is None:
            output(self.out_lck, 'No response from tracker. Login failed')
            self.procedure_lck.release()
        elif response_message[0:4] == 'ALOG':
            self.session_id = None
            # TODO: fare il check della connessione sulla socket dopo 60'
            self.tracker.close()  # Chiusura della connessione
            if self.pool:
                while self.pool.tasks.qsize() > 0:
                    output(self.out_lck, 'Wait finish upload')
                    time.sleep(10)
            output(self.out_lck, 'Wait 60 seconds to finish')
            time.sleep(60)
            output(self.out_lck, 'Logout completed, parts removed from the network: ' + str(n_parts))
            self.procedure_lck.release()
            exit()
        elif response_message[0:4] == "NLOG":
            output(self.out_lck, 'Logout denied, parts already downloaded by other peers: ' + str(n_parts))
            self.procedure_lck.release()
        else:
            output(self.out_lck, 'Error: unknown response from tracker.\n')
            self.procedure_lck.release()

    def share(self):
        # IPP2P:RND <> IPT:3000
        # > “ADDR”[4B].SessionID[16B].LenFile[10B].LenPart[6B].Filename[100B].Filemd5_i[32B]
        # < “AADR”[4B].  # part[8B]

        self.procedure_lck.acquire()

        found = False
        while not found:
            output(self.out_lck, '\nSelect a file to share (\'c\' to cancel):')
            for idx, file in enumerate(self.files_list):
                output(self.out_lck, str(idx) + ": " + file.name)

            try:
                option = input()
            except SyntaxError:
                option = None

            if option is None:
                output(self.out_lck, 'Please select an option')
            elif option == "c":
                break
            else:
                try:
                    int_option = int(option)
                except ValueError:
                    output(self.out_lck, "A number is required")
                else:
                    for idx, file in enumerate(self.files_list):  # Ricerca del file selezionato
                        if idx == int_option:
                            found = True

                            output(self.out_lck, "Adding file " + file.name)

                            len_part = self.part_size  # 256KB

                            ip_concat = self.my_ipv4 + self.my_ipv6
                            bytes_ip = str.encode(ip_concat)

                            LenFile = str(os.path.getsize(self.path+"/"+file.name)).zfill(10)
                            LenPart = str(len_part).zfill(6)
                            FileName = file.name.ljust(100)
                            Filemd5_i = hashfile_ip(open(self.path+"/"+file.name, "rb"), hashlib.md5(), bytes_ip)

                            msg = "ADDR" + str(self.session_id) + str(LenFile) + str(LenPart) + str(FileName) + str(Filemd5_i)

                            response_message = None

                            try:
                                self.check_connection()

                                self.tracker.send(msg.encode('utf-8'))
                                self.print_trigger.emit(
                                    '=> ' + str(self.tracker.getpeername()[0]) + '  ' + msg[0:4] + '  ' + self.session_id +
                                    '  ' + str(LenFile).strip("") + '  ' + str(LenPart).strip("") + '  ' + str(FileName).strip("") +
                                    '  ' + str(Filemd5_i).strip(""), "00")
                                self.print_trigger.emit("", "00")  # Space

                                response_message = recvall(self.tracker, 4).decode('ascii')

                            except Exception as e:
                                self.print_trigger.emit('Error: ' + str(e), '01')
                                self.print_trigger.emit("", "00")  # Space

                            if response_message[:4] == 'AADR':

                                part_n = int(recvall(self.tracker, 8).decode('ascii'))
                                self.print_trigger.emit(
                                    '<= ' + str(self.tracker.getpeername()[0]) + '  ' + response_message[0:4] + '  ' +
                                    str(part_n), '02')
                                self.print_trigger.emit("", "00")  # Space

                                output(self.out_lck, "File successfully shared, parts: " + str(part_n))

                                # Salvo file condiviso sul database
                                self.dbConnect.insert_file(FileName.strip(), Filemd5_i, LenFile, LenPart)

                            else:
                                output(self.out_lck, 'Error: unknown response from tracker.\n')

                    if not found:
                        output(self.out_lck, 'Option not available')

        self.procedure_lck.release()

    def look(self):
        #IPP2P:RND <> IPT:3000
        #> “LOOK”[4B].SessionID[16B].Ricerca[20B]
        #< “ALOO”[4B].  # idmd5[3B].{Filemd5_i[32B].Filename_i[100B].LenFile[10B].LenPart[6B]}(i = 1..  # idmd5)

        self.procedure_lck.acquire()

        output(self.out_lck, 'Insert search term:')
        ricerca = None
        while ricerca is None:
            try:
                ricerca = input()  # Inserimento del parametro di ricerca
            except SyntaxError:
                ricerca = None

            if ricerca is None:
                output(self.out_lck, 'Please insert a search term')

        output(self.out_lck, "Searching files that match: " + ricerca)

        msg = 'LOOK' + self.session_id + ricerca.ljust(20)

        response_message = None
        printable_response = None
        try:
            self.check_connection()

            self.tracker.send(msg.encode('utf-8'))
            self.print_trigger.emit(
                '=> ' + str(self.tracker.getpeername()[0]) + '  ' + msg[0:4] + '  ' + self.session_id +
                '  ' + ricerca.ljust(20), "00")
            self.print_trigger.emit("", "00")  # Space

            response_message = recvall(self.tracker, 4).decode('ascii')
            printable_response = response_message + '  '

        except Exception as e:
            self.print_trigger.emit('Error: ' + str(e), '01')
            self.print_trigger.emit("", "00")  # Space

        if response_message is None:
            output(self.out_lck, 'No response from tracker. Look failed')
            self.procedure_lck.release()
        elif response_message[0:4] == 'ALOO':

            idmd5 = None
            try:
                idmd5 = recvall(self.tracker, 3).decode('ascii')  # Numero di identificativi md5

            except Exception as e:
                self.print_trigger.emit('Error: ' + str(e), '01')
                self.print_trigger.emit("", "00")  # Space

            if idmd5 is None:
                output(self.out_lck, 'idmd5 is blank.')
                self.procedure_lck.release()
            else:
                try:
                    printable_response += idmd5 + '  '
                    idmd5 = int(idmd5)
                except ValueError:
                    output(self.out_lck, "idmd5 is not a number")
                else:
                    if idmd5 == 0:
                        output(self.out_lck, "No results found for search term: " + ricerca)
                        self.procedure_lck.release()
                    elif idmd5 > 0:  # At least one result
                        available_files = []

                        try:
                            for idx in range(0, idmd5):  # Per ogni identificativo diverso si ricevono:
                                # md5, nome del file, numero di copie, elenco dei peer che l'hanno condiviso

                                file_i_md5 = recvall(self.tracker, 32).decode('ascii')
                                printable_response += file_i_md5 + '  '
                                file_i_name = recvall(self.tracker, 100).decode('ascii').strip()
                                printable_response += file_i_name + '  '
                                len_file_i = recvall(self.tracker, 10).decode('ascii')
                                printable_response += len_file_i + '  '
                                len_part_i = recvall(self.tracker, 6).decode('ascii')
                                printable_response += len_part_i + '  '

                                available_files.append({"name": file_i_name,
                                                        "md5": file_i_md5,
                                                        "len_file": len_file_i,
                                                        "len_part": len_part_i
                                                        })

                        except Exception as e:
                            output(self.out_lck, 'Error: ' + str(e))

                        self.print_trigger.emit(
                            '<= ' + str(self.tracker.getpeername()[0]) + '  ' + printable_response, '02')
                        self.print_trigger.emit("", "00")  # Space

                        if len(available_files) == 0:
                            output(self.out_lck, "No results found for search term: " + ricerca)
                            self.procedure_lck.release()
                        else:
                            output(self.out_lck, "\nSelect a file to download ('c' to cancel): ")
                            for idx, file in enumerate(available_files):  # visualizza i risultati della ricerca
                                output(self.out_lck, str(idx) + ": " + file['name'])

                            selected_file = None
                            while selected_file is None:
                                try:
                                    option = input()  # Selezione del file da scaricare
                                except SyntaxError:
                                    option = None

                                if option is None:
                                    output(self.out_lck, 'Please select an option')
                                elif option == 'c':
                                    self.procedure_lck.release()
                                    return
                                else:
                                    try:
                                        selected_file = int(option)
                                    except ValueError:
                                        output(self.out_lck, "A number is required")

                            file_to_download = available_files[selected_file]  # Recupero del file selezionato dalla lista dei risultati

                            self.procedure_lck.release()

                            # Avvio un thread che esegue la fetch ogni 60(10) sec
                            # self.fetch_scheduler = threading.Timer(10, self.fetch, [file_to_download])
                            # self.fetch_scheduler.start()

                            # La prima fetch deve partire subito
                            self.fetch(file_to_download)

                            # Poi ogni 60(10) sec
                            self.fetch_scheduler = Scheduler(60, self.fetch, file_to_download)  # Auto start

                            # Aspetto che la prima fetch abbia terminato
                            while self.fetching:
                                time.sleep(1)

                            output(self.out_lck, "\nStart download file?: ")
                            output(self.out_lck, "1: Yes")
                            output(self.out_lck, "2: No")

                            start_download = None
                            while start_download is None:
                                try:
                                    option = input()
                                except SyntaxError:
                                    option = None

                                if option is None:
                                    output(self.out_lck, 'Please select an option')
                                else:
                                    try:
                                        start_download = int(option)
                                    except ValueError:
                                        output(self.out_lck, "A number is required")

                            if start_download == 1:
                                # AVVIO IL THREAD DI GESTIONE DEL DOWNLOAD
                                mainGet = threading.Thread(target=self.get_file, args=(file_to_download['md5'],
                                                                                       file_to_download['name'],
                                                                                       file_to_download['len_file'],
                                                                                       file_to_download['len_part']))
                                mainGet.start()

                                # Aggiorno la progress bar principale
                                output(self.out_lck, "Downloading file")
                                down_progress = 0
                                self.download_progress_trigger.emit(down_progress, file_to_download['name'])
                            else:
                                output(self.out_lck, "Download aborted")

        else:
            output(self.out_lck, 'Error: unknown response from tracker.\n')
            self.procedure_lck.release()

    def fetch(self, file):
        # IPP2P:RND <> IPT:3000
        # > “FCHU”[4B].SessionID[16B].Filemd5_i[32B]
        # < “AFCH”[4B].#hitpeer[3B].{IPP2P_i[55B].PP2P_i[5B].PartList_i[#part8]}(i = 1..# hitpeer)

        self.fetching = True
        self.procedure_lck.acquire()

        n_parts = int(math.ceil(float(file['len_file']) / float(file['len_part'])))  # 1024

        n_parts8 = int(math.ceil(float(float(n_parts)/8)))  # 128

        output(self.out_lck, "\nFetching parts informations about file " + file['name'])
        msg = "FCHU" + self.session_id + file['md5']

        response_message = None
        printable_response = None
        try:
            self.check_connection()

            self.tracker.sendall(msg.encode('utf-8'))
            self.print_trigger.emit('=> ' + str(self.tracker.getpeername()[0]) + '  ' + msg[0:4] + '  ' +
                                    self.session_id + '  ' + file['md5'], "00")
            self.print_trigger.emit("", "00")  # Space

            response_message = recvall(self.tracker, 4).decode('ascii')
            printable_response = response_message + '  '

        except Exception as e:
            self.print_trigger.emit('Error: ' + str(e), '01')
            self.print_trigger.emit("", "00")  # Space

        if response_message is None:
            output(self.out_lck, 'No response from tracker. Fetch failed')
            self.procedure_lck.release()
            self.fetching = False

        elif response_message[0:4] == 'AFCH':
            # numero di peer che hanno interesse nel file selezionato
            n_hitpeers = recvall(self.tracker, 3).decode('ascii')
            try:
                printable_response += n_hitpeers + '  '
                n_hitpeers = int(n_hitpeers)
            except ValueError:
                output(self.out_lck, "n_hitpeers is not a number")
            else:
                if n_hitpeers is not None and n_hitpeers > 0:
                    hitpeers = []

                    # aggiorno la lista di hitpeers
                    for i in range(0, n_hitpeers):
                        hitpeer_ipv4 = recvall(self.tracker, 16).decode('ascii').replace("|", "")
                        printable_response += hitpeer_ipv4 + '  '
                        hitpeer_ipv6 = recvall(self.tracker, 39).decode('ascii')
                        printable_response += hitpeer_ipv6 + '  '
                        hitpeer_port = recvall(self.tracker, 5).decode('ascii')
                        printable_response += hitpeer_port + '  '
                        hitpeer_partlist = recvall(self.tracker, n_parts8)
                        #printable_response += hitpeer_partlist.decode('utf-8') + '  '

                        hitpeers.append({
                            "ipv4": hitpeer_ipv4,
                            "ipv6": hitpeer_ipv6,
                            "port": hitpeer_port,
                            "part_list": hitpeer_partlist
                        })

                    self.print_trigger.emit('<= ' + str(self.tracker.getpeername()[0]) + '  ' + printable_response, '02')
                    self.print_trigger.emit("", "00")  # Space

                    if hitpeers:
                        # cerco la tabella delle parti di cui fare il download se non esiste la creo

                        download = self.dbConnect.get_download(file['md5'])

                        if download:
                            parts = download['parts']
                        else:
                            self.dbConnect.insert_download(file['name'], file['md5'], file['len_file'], file['len_part'])
                            parts = []

                        # scorro i risultati della FETCH ed aggiorno la lista delle parti in base alla disponibilità
                        for hp in hitpeers:
                            part_count = 0
                            # VALIDO PER part_list salvata come stringa di caratteri ASCII

                            for c in hp['part_list']:
                                #bits = bin(ord(c)).replace("0b", "").replace("b", "").zfill(8)  # Es: 0b01001101
                                #bits = bin(int(c,16))[2:]
                                bits = ascii(c)

                                for bit in bits:

                                    if int(bit) == 1:  # se la parte è disponibile
                                        part = [part for part in parts if part['n'] == part_count]

                                        if len(part) > 0:
                                            peers = parts[part_count-1]['peers'] if parts[part_count-1]['peers'] is not None else []

                                            exists = [True for peer in peers if (peer['ipv4'] == hp['ipv4']) or (peer['ipv6'] == hp['ipv6'])]

                                            if not exists:
                                                peers.append({
                                                             "ipv4": hp['ipv4'],
                                                             "ipv6": hp['ipv6'],
                                                             "port": hp['port']
                                                         })

                                                parts[part_count - 1]['occ'] = int(parts[part_count - 1]['occ']) + 1

                                            parts[part_count-1]['peers'] = peers
                                        else:
                                            peers = []
                                            peers.append({
                                                         "ipv4": hp['ipv4'],
                                                         "ipv6": hp['ipv6'],
                                                         "port": hp['port']
                                                     })
                                            parts.append({
                                                     "n": part_count,
                                                     "occ": 1,
                                                     "downloaded": "false",
                                                     "peers": peers
                                                 })

                                        part_count += 1
                                    else:
                                        part_count += 1

                        # ordino la lista delle parti in base alle occorrenze in modo crescente
                        sorted_parts = sorted(parts, key=lambda k: k['occ'])

                        # aggiorno la lista già ordinata
                        self.dbConnect.update_download_parts(file['md5'], sorted_parts)

                        output(self.out_lck, "Part table updated, fetch succeeded.")
                        self.fetching = False
                        self.procedure_lck.release()

                else:
                    output(self.out_lck, 'No peers found.\n')
                    self.fetching = False
                    self.procedure_lck.release()
        else:
            output(self.out_lck, 'Error: unknown response from tracker.\n')
            self.fetching = False
            self.procedure_lck.release()

    def get_file(self, md5, file_name, len_file, len_part):

        # Aspetto che la fetch abbia terminato
        while self.fetching:
            time.sleep(1)

        # Inserisco il file nel database in modo che le parti siano disponibili al download degli altri peer
        self.dbConnect.insert_file(file_name, md5, len_file, len_part)

        parts_table = self.dbConnect.get_download(md5)

        if parts_table:
            parts = parts_table['parts']

            # POOL THREAD PER IL DOWNLOAD DELLE PARTI
            # 1) Inizio il Thread pool con il numero desiderato di threads
            self.pool = ThreadPool(self.parallel_downloads)

            download_idx = 0
            completed = self.dbConnect.downloading(md5)
            self.download_progress_trigger.emit(0, file_name)

            # while threads < 5 or (len(parts) > download_idx):
            while not completed:
                while self.pool.tasks.qsize() < self.parallel_downloads and not completed:
                    if download_idx < len(parts):
                        if not parts[download_idx]['downloaded'] or parts[download_idx]['downloaded'] == "false":
                            part_n = parts[download_idx]['n']

                            # 2) Aggiungo it task in una coda
                            self.pool.add_task(self.download, md5, part_n, file_name)
                            # threads += 1
                            download_idx += 1
                        else:
                            download_idx += 1
                    else:
                        download_idx = 0
                # 3) Aspetto il completamento dei task
                self.pool.wait_completion()

                # Ricarico la lista delle parti che dovrebbe essere stata aggiornata con le parti scaricate
                parts_table = self.dbConnect.get_download(md5)
                parts = parts_table['parts']

                # Ricomincio a scorrere la tabella dall'inizio perchè la fetch potrebbe cambiarne l'ordine
                download_idx = 0

                completed = self.dbConnect.downloading(md5)

            self.fetch_scheduler.stop()

            self.dbConnect.remove_download(md5)

            # Unisco i file
            list_parts = []

            for root, dirs, files in os.walk("./received/temp/"):
                for f in files:
                    list_parts.append("./received/temp/" + f)

            output(self.out_lck, "Joining parts")
            join_parts_mac(list_parts, "./received/" + file_name)

            self.download_progress_trigger.emit(100, file_name)

            output(self.out_lck, "Download completed")

        else:
            output(self.out_lck, 'Error: parts table not found.\n')

    def download(self, md5, n_part, file_name):
        # IPP2P:RND <> IPP2P:PP2P
        # > “RETP”[4B].Filemd5_i[32B].PartNum[8B]
        # < “AREP”[4B].  # chunk[6B].{Lenchunk_i[5B].data[LB]}(i=1..#chunk)

        # aspetto che la fetch abbia terminato
        while self.fetching:
            time.sleep(1)  # 1 sec

        part = self.dbConnect.get_downloadable_part(md5, n_part)
        download = None
        while download is None:  # provo a connettermi ad uno dei peer finchè non ne trovo uno online
            selected_peer = random.choice(list(part['peers']))

            if not selected_peer['ipv4'] == self.my_ipv4 or not selected_peer['ipv6'] == self.my_ipv6:
                try:
                    c = connection.Connection(selected_peer['ipv4'], selected_peer['ipv6'], selected_peer['port'], self.print_trigger,
                                              "0")  # Inizializzazione della connessione verso il peer
                    c.connect()
                    download = c.socket

                except Exception as msg:
                    download = None
            else:
                download = None

        if download is None:
            output(self.out_lck, "Error: No available connections for part " + str(n_part))
        else:
            # output(self.out_lck, "Downloading part " + str(n_part) + " from " + selected_peer['ipv4'])

            msg = "RETP" + md5 + str(n_part).zfill(8)

            response_message = None
            try:

                download.send(msg.encode('utf-8'))
                self.print_trigger.emit('=> ' + str(download.getpeername()[0]) + '  ' + msg[0:4] + '  ' +
                                        md5 + '  ' + msg[36:], "00")
                self.print_trigger.emit("", "00")  # Space

                response_message = recvall(download, 4).decode('ascii')

            except Exception as e:
                self.print_trigger.emit('Error: ' + str(e), '01')

            else:
                if response_message[:4] == 'AREP':
                    n_chunks = recvall(download, 6).decode('ascii')  # Numero di parti del file da scaricare

                    self.print_trigger.emit('<= ' + str(download.getpeername()[0]) + '  ' + response_message[0:4] +
                                            '  ' + n_chunks, '02')
                    self.print_trigger.emit("", "00")  # Space

                    # Rimozione gli 0 dal numero di parti e converte in intero
                    n_chunks = int(str(n_chunks).lstrip('0'))
                    data = ''

                    for i in range(0, n_chunks):
                        try:
                            chunk_length = recvall(download, 5).decode('ascii')  # Ricezione dal peer la lunghezza della parte di file
                            data += recvall(download, int(chunk_length)) .decode('ascii') # Ricezione dal peer la parte del file

                            # Updating progress bar
                            progress = round(float(i) * 100 / float(n_chunks), 0)
                            self.download_trigger.emit(str(n_part), str(download.getpeername()[0]), progress)

                        except IOError as e:
                            # output(self.out_lck, 'IOError: ' + str(e))
                            self.print_trigger.emit('IOError: ' + str(e), '01')
                            break
                        except Exception as e:
                            # output(self.out_lck, 'Error: ' + str(e))
                            self.print_trigger.emit('Error: ' + str(e), '01')
                            break

                    download.shutdown(1)
                    download.close()

                    # Salvo la parte in un file
                    file_out = open("./received/temp/" + file_name + '.%08d' % n_part, 'wb')
                    file_out.write(data)
                    file_out.close()

                    # Aggiorno la tabella di download segnando la parte scaricata
                    self.dbConnect.update_download(md5, n_part)

                    # Aggiorno la progress bar principale
                    n_parts, tot_parts = self.dbConnect.get_download_progress(md5)
                    down_progress = int(n_parts * 100 / tot_parts)
                    self.download_progress_trigger.emit(down_progress, file_name)

                    # Notifica al tracker del download avvenuto
                    self.notify_tracker(md5, n_part)

                else:
                    output(self.out_lck, 'Error: unknown response from peer.\n')

    def notify_tracker(self, md5, n_part):
        # IPP2P:RND <> IPT:3000
        # > “RPAD”[4B].SessionID[16B].Filemd5_i[32B].PartNum[8B]
        # < “APAD”[4B].  # Part[8B]

        self.procedure_lck.acquire()

        msg = "RPAD" + self.session_id + md5 + str(n_part).zfill(8)
        response_message = None

        try:
            self.check_connection()

            self.tracker.sendall(msg.encode('utf-8'))
            self.print_trigger.emit('=> ' + str(self.tracker.getpeername()[0]) + '  ' + msg[0:4] + '  ' +
                                    self.session_id + '  ' + md5 + '  ' + str(n_part), "00")
            self.print_trigger.emit("", "00")  # Space
            # output(self.out_lck, msg)
            response_message = recvall(self.tracker, 4).decode('ascii')

        except Exception as e:
            self.print_trigger.emit('Error: ' + str(e), '01')

        if response_message is None:
            output(self.out_lck, 'No response from tracker. Download failed')
            self.procedure_lck.release()
        elif response_message[0:4] == 'APAD':
            num_part = recvall(self.tracker, 8).decode('ascii')
            self.print_trigger.emit('<= ' + str(self.tracker.getpeername()[0]) + '  ' + response_message[0:4] +
                                    '  ' + num_part, '02')
            self.print_trigger.emit("", "00")  # Space
            num_part = int(num_part)
            #output(self.out_lck, response_message[0:4])
            # output(self.out_lck, "Tracker successfully notified for part " + str(num_part))
            self.procedure_lck.release()
        else:
            output(self.out_lck, "Unknown response from tracker. Download failed")
            self.procedure_lck.release()

    '''
        Helper methods
    '''
    def check_connection(self):
        if not self.alive(self.tracker):
            c = connection.Connection(self.track_ipv4, self.track_ipv6, self.track_port,
                                      self.print_trigger, "0")  # Creazione connessione con il tracker
            c.connect()
            self.tracker = c.socket

    def alive(self, socket):
        try:
            if socket.socket() != None:
                return True
        except Exception:
            pass
            return False

