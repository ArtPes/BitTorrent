# coding=utf-8
import socket, os, hashlib, select, sys, time

# sys.path.insert(1, '/home/massa/Documenti/PycharmProjects/P2PKazaa')
from random import randint
import threading
from dbmodules.dbconnection import *
from PyQt4 import QtCore, QtGui
from helpers import *


class Peer_Server(threading.Thread):
    """
        Ascolta sulla porta 6000
        Supernodo: Gestisce le comunicazioni con gli altri i supernodi e l'invio dei file: SUPE, ASUP, QUER, AQUE, RETR
        Peer: Gestisce la propagazione dei pacchetti SUPE a tutti i vicini e l'invio dei file
    """
    # TODO cambiare sul mac con ./fileCondivisi
    path = "./fileCondivisi"


    def __init__(self, (client, address), dbConnect, output_lock, print_trigger, my_ipv4, my_ipv6, my_port):
        #QtCore.QThread.__init__(self, parent=None)
        threading.Thread.__init__(self)
        self.client = client
        self.address = address
        self.size = 1024
        self.dbConnect = dbConnect
        self.output_lock = output_lock
        self.print_trigger = print_trigger
        self.my_ipv4 = my_ipv4
        self.my_ipv6 = my_ipv6
        self.my_port = my_port

    def run(self):
        conn = self.client
        #cmd = recvall(conn, self.size)
        try:
            cmd = conn.recv(self.size)
        except socket.error:
            pass
        else:
            while len(cmd) > 0:
                if cmd[:4] == 'RETP':
                    #IPP2P:RND <> IPP2P:PP2P
                    #> “RETP”[4B].Filemd5_i[32B].PartNum[8B]
                    #< “AREP”[4B].  # chunk[6B].{Lenchunk_i[5B].data[LB]}(i=1..#chunk)

                    #file_md5 = recvall(conn, 32)
                    #part_num = int(recvall(conn, 8))
                    file_md5 = cmd[4:36]
                    part_num = int(cmd[36:44])

                    self.print_trigger.emit("<= " + str(self.address[0]) + "  " + cmd[0:4] + "  " + file_md5 + "  " + str(part_num), "10")
                    self.print_trigger.emit("", "00")  # Space

                    db_file = self.dbConnect.get_file(file_md5)

                    partsize = int(db_file['len_part'])
                    #partsize = 262144

                    # Se il percorso in fileCondivisi non esiste significa che il file non è mio ma lo sto scaricando
                    # quindi vado a cercare la parte in received
                    if os.path.exists(self.path + "/" + db_file['name']):
                        file = open(self.path + "/" + db_file['name'], 'rb')

                        part_count = 0
                        requested_part = None
                        buf = file.read(partsize)
                        while len(buf) > 0:
                            if part_count == part_num:
                                requested_part = buf
                                break
                            else:
                                part_count += 1
                                buf = file.read(partsize)

                    elif os.path.exists("./received/" + db_file['name']):
                        # Il file è tra quelli scaricati ed è completato
                        file = open("./received/" + db_file['name'], 'rb')

                        part_count = 0
                        requested_part = None
                        buf = file.read(partsize)
                        while len(buf) > 0:
                            if part_count == part_num:
                                requested_part = buf
                                break
                            else:
                                part_count += 1
                                buf = file.read(partsize)
                    else:
                        # Il file è ancora in download quindi cerco la parte in received/temp

                        requested_part = None

                        for root, dirs, files in os.walk("./received/temp/"):
                            for file in files:
                                if file == (db_file['name'] + '.%08d' % part_num):
                                    requested_part_file = open("./received/temp/" + db_file['name'] + '.%08d' % part_num)
                                    requested_part = requested_part_file.read(partsize)

                    if requested_part:
                        chunk_size = 1024
                        n_chunks = int(len(requested_part) // chunk_size)  # Calcolo del numero di parti
                        resto = len(requested_part) % chunk_size  # Eventuale resto

                        if resto != 0.0:
                            n_chunks += 1

                        try:
                            chunks_sent = 0
                            offset = 0

                            buff = requested_part[offset: offset + chunk_size]  # Lettura del primo chunk

                            msg = 'AREP' + str(n_chunks).zfill(
                                6)  # Risposta alla richiesta di download, deve contenere ARET ed il numero di chunks che saranno inviati

                            conn.sendall(msg)
                            self.print_trigger.emit("=> " + str(self.address[0]) + "  " + msg[0:4] + '  ' + msg[4:10], "12")
                            #output(self.output_lock, "\r\nUpload Started")

                            while len(buff) == chunk_size:  # Invio dei chunks
                                try:
                                    msg = str(len(buff)).zfill(5) + buff
                                    conn.sendall(msg)  # Invio di
                                    chunks_sent += 1

                                    #output(self.output_lock, str(part_num) + " : " + str(chunks_sent))
                                    # update_progress(self.output_lock, chunks_sent, n_chunks,
                                    #                 'Uploading ' + file['name'])  # Stampa a video del progresso dell'upload

                                    offset += chunk_size
                                    buff = requested_part[offset: offset + chunk_size]  # Lettura chunk successivo
                                except socket.error, msg:
                                    self.print_trigger.emit("Connection Error: %s" % msg, '11')
                                except Exception as e:
                                    self.print_trigger.emit('Error: ' + e.message, '11')

                            if len(buff) != 0:  # Invio dell'eventuale resto, se più piccolo di chunk_size
                                try:
                                    msg = str(len(buff)).zfill(5) + buff
                                    conn.sendall(msg)

                                except socket.error, msg:
                                    self.print_trigger.emit("Connection Error: %s" % msg, '11')
                                except Exception as e:
                                    self.print_trigger.emit('Error: ' + e.message, '11')

                            #output(self.output_lock, "\r\nUpload Completed")

                        except socket.error, msg:
                            self.print_trigger.emit("Connection Error: %s" % msg, '11')
                        except Exception as e:
                            self.print_trigger.emit('Error: ' + e.message, '11')
                        except EOFError:
                            self.print_trigger.emit("Error: You have read a EOF char", '11')

                        # Spazio
                        self.print_trigger.emit("", "10")
                    else:
                        self.print_trigger.emit("Error: part " + str(part_num) + " not found", '11')
                else:
                    self.print_trigger.emit("\nError: Command" + cmd + " not recognized", '11')

                #conn.shutdown(1)
                conn.close()
                break
                #cmd = recvall(conn, self.size)
                # try:
                #     cmd = conn.recv(self.size)
                # except socket.error:
                #     pass