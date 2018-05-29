# coding=utf-8
# coding=utf-8
import socket, os, hashlib, select, sys, time
import math

sys.path.insert(1, 'insert_path_of_directory')
from random import randint
import threading
from dbmodules.dbconnection import *
from helpers import *
from PyQt5 import QtCore, QtGui, QtWidgets



class Tracker_Server(threading.Thread):
    """
        Ascolta sulla porta 3000
        Supernodo: Gestisce le comunicazioni tra directory e i peer: LOGI, LOGO, ADDF, DELF, FIND
        Peer: non utilizzata
    """

    def __init__(self, arg, dbConnect, output_lock, print_trigger, my_ipv4, my_ipv6, my_port):
        # QtCore.QThread.__init__(self, parent=None)
        threading.Thread.__init__(self)
        self.client = arg[0]
        self.address = arg[1]
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
            cmd = conn.recv(self.size).decode("utf-8")
        except socket.error:
            pass
        else:
            while len(cmd) > 0:


                if cmd[:4] == 'LOGI':
                    # IPP2P:RND <> IPT:3000
                    # > “LOGI”[4B].IPP2P[55B].PP2P[5B]
                    # > LOGI172.030.008.001|fc00:0000:0000:0000:0000:0000:0008:000106000
                    # < “ALGI”[4B].SessionID[16B]

                    ipv4 = cmd[4:19]
                    ipv6 = cmd[20:59]
                    port = cmd[59:64]
                    self.print_trigger.emit(
                        "<= " + str(self.address[0]) + "  " + cmd[:4] + '  ' + ipv4 + '  ' + ipv6 + '  ' + str(port), "10")
                    # Spazio
                    self.print_trigger.emit("", "10")

                    sessionId = self.dbConnect.insert_session(ipv4, ipv6, port)
                    msg = 'ALGI' + sessionId
                    try:
                        conn.send(msg.encode('utf-8'))
                        self.print_trigger.emit("=> " + str(self.address[0]) + "  " + msg[0:4] + '  ' + sessionId, "12")
                    except socket.error as msg:
                        self.print_trigger.emit("Connection Error: %s" % msg, "11")
                    except Exception as e:
                        self.print_trigger.emit('Error: ' + e, "11")
                    # Spazio
                    self.print_trigger.emit("", "10")

                elif cmd[:4] == 'LOGO':
                    # IPP2P:RND <> IPT:3000
                    # > “LOGO”[4B].SessionID[16B]
                    # 1 < “NLOG”[4B].  # partdown[10B]
                    # 2 < “ALOG”[4B].  # partown[10B]

                    session_Id = cmd[4:20]
                    self.print_trigger.emit("<= " + str(self.address[0]) + "  " + cmd[0:4] + "  " + session_Id, "10")

                    # Spazio
                    self.print_trigger.emit("", "10")

                    delete = self.dbConnect.new_remove_session(session_Id)
                    if delete[0] is 'T':
                        print("logout")
                        # logout concesso
                        # TODO: finire
                        partown = delete[1:11]
                        msg = "ALOG" + str(partown).zfill(10)
                        try:
                            conn.send(msg.encode('utf-8'))
                            # TODO: da finire la funzione che conta le parti
                            self.print_trigger.emit("=> " + "ALOG" + "  " + str(partown).zfill(8), "12")
                        except socket.error as msg:
                            self.print_trigger.emit("Connection Error: %s" % msg, "11")
                        except Exception as e:
                            self.print_trigger.emit('Error: ' + e, "11")
                        # Spazio
                        self.print_trigger.emit("", "10")
                    else:
                        print("not logout")
                        # logout non concesso
                        partdown = delete[1:11]
                        msg = "NLOG" + str(partdown).zfill(10)
                        try:
                            conn.send(msg.encode('utf-8'))
                            self.print_trigger.emit("=> " + "NLOG" + " " + str(partdown).zfill(8), "12")
                        except socket.error as msg:
                            self.print_trigger.emit("Connection Error: %s" % msg, "11")
                        except Exception as e:
                            self.print_trigger.emit('Error: ' + e, "11")
                        # Spazio
                        self.print_trigger.emit("", "10")


                elif cmd[:4] == 'ADDR':
                    # IPP2P:RND <> IPT:3000
                    # > “ADDR”[4B].SessionID[16B].LenFile[10B].LenPart[6B].Filename[100B].Filemd5_i[32B]
                    # < “AADR”[4B].  # part[8B]

                    session_id = cmd[4:20]
                    len_file = cmd[20:30]
                    len_part = cmd[30:36]
                    name = cmd[36:136].strip(" ")
                    md5 = cmd[136:168]

                    num_part = int(math.ceil(float(len_file)/float(len_part)))

                    self.print_trigger.emit(
                        "<= " + str(self.address[0]) + "  " + cmd[0:4] + "  " + session_id + "  " + len_file + "  " +
                        len_part+"  "+name+"  "+md5, "10")
                    # Spazio
                    self.print_trigger.emit("", "10")

                    self.dbConnect.insert_peer(name, md5, len_file, len_part, session_id)
                    #risposta

                    response = "AADR" + str(num_part).zfill(8)

                    try:
                        conn.sendall(response.encode("utf-8"))
                        self.print_trigger.emit("=> " + "AADR" + " " + str(num_part).zfill(8), "12")

                    except socket.error as msg:
                        self.print_trigger.emit('Socket Error: ' + str(response), '11')
                    except Exception as e:
                        self.print_trigger.emit('Error: ' + str(e), '11')

                    self.print_trigger.emit("File succesfully shared by " + str(self.address[0]), "12")
                    # Spazio
                    self.print_trigger.emit("", "10")

                elif cmd[:4] == 'LOOK':
                    # IPP2P:RND <> IPT:3000
                    # > “LOOK”[4B].SessionID[16B].Ricerca[20B]
                    # < “ALOO”[4B].#idmd5[3B].{Filemd5_i[32B].Filename_i[100B].LenFile[10B].LenPart[6B]}(i = 1..  # idmd5)
                    session_id = cmd[4:20]
                    term = cmd[20:40]

                    self.print_trigger.emit(
                        "<= " + str(self.address[0]) + "  " + cmd[0:4] + "  " + session_id + "  " + term + "  ", "10")

                    idmd5 = self.dbConnect.get_files_tracker(term)
                    idmd5_count = str(idmd5.count()).zfill(3)

                    msg = "ALOO" + idmd5_count
                    print_msg = "ALOO" + "  " + idmd5_count

                    for file in idmd5:
                        msg += str(file['md5']).ljust(32) + str(file['name']).ljust(100) + str(file['len_file']).zfill(10) + str(file['len_part']).zfill(6)
                        print_msg += "  " + str(file['md5']).ljust(32) + "  " + str(file['name']).ljust(100) + "  " + str(file['len_file']).zfill(10) + "  " + str(file['len_part']).zfill(6)

                    try:
                        conn.sendall(msg.encode('utf-8'))

                        self.print_trigger.emit(
                            "=> " + str(conn.getpeername()[0]) + "  " + print_msg, "12")
                        # Spazio
                        self.print_trigger.emit("", "10")

                    except socket.error as msg:
                        self.print_trigger.emit('Socket Error: ' + str(msg), '11')
                    except Exception as e:
                        self.print_trigger.emit('Error: ' + e, '11')

                elif cmd[:4] == 'FCHU':
                    # IPP2P:RND <> IPT:3000
                    # > “FCHU”[4B].SessionID[16B].Filemd5_i[32B]
                    # < “AFCH”[4B].#hitpeer[3B].{IPP2P_i[55B].PP2P_i[5B].PartList_i[#part8]}(i = 1..# hitpeer)

                    # file = {
                    #     "name": "prova.avi",
                    #     "md5": "DYENCNYDABKASDKJCBAS8441132A57ST",
                    #     "len_file": "1073741824",  # 1GB
                    #     "len_part": "1048576"  # 256KB
                    # }
                    #
                    # n_parts = int(file['len_file']) / int(file['len_part'])  # 1024
                    #
                    # n_parts8 = int(round(n_parts / 8))  # 128

                    session_id = cmd[4:20]
                    file_md5 = cmd[20:52]

                    self.print_trigger.emit(
                        "<= " + str(self.address[0]) + "  " + cmd[0:4] + "  " + session_id + " " + file_md5, "10")
                    # Spazio
                    self.print_trigger.emit("", "10")

                    hitpeers = self.dbConnect.get_parts(file_md5)

                    # TODO: devo eliminare me stesso dalla lista dei peer

                    n_hitpeers = str(len(hitpeers)).zfill(3)

                    msg = "AFCH" + n_hitpeers

                    print_msg = "AFCH" + "  " + n_hitpeers
                    for peer in hitpeers:
                        ascii_part_list = bytearray()
                        n = 8
                        parts_8 = [peer['part_list'][i:i+n] for i in range(0, len(peer['part_list'])+1, n)]

                        #
                        # L'ultima parte può essere più corta quindi vanno aggiunti degli zeri alla fine, altrimenti python
                        # li mette all'inizio e cambia il significato della partlist
                        for part in parts_8:
                            if len(part) == 8:
                                ascii_part_list.append(int(part, 2))
                            else:
                                part = part.ljust(8, "0")
                                ascii_part_list.append(int(part, 2))
                        #print ascii_part_list

                        msg += str(peer['ipv4']) + "|" + str(peer['ipv6']) + str(peer['port'])
                        #print(msg.encode('ascii'))
                        print_msg += "  " + str(peer['ipv4']) + "  " + str(peer['ipv6']) + "  " + str(peer['port']) + \
                                     "  " + str(ascii_part_list)

                    try:
                        msg = msg.encode('utf-8')

                        conn.sendall(msg)
                        conn.sendall(ascii_part_list)

                        self.print_trigger.emit(
                            "=> " + str(conn.getpeername()[0]) + "  " + print_msg, "12")
                        # Spazio
                        self.print_trigger.emit("", "10")

                    except socket.error as msg:
                        self.print_trigger.emit('Socket Error: ' + str(msg), '11')
                    except Exception as e:
                        self.print_trigger.emit('Error: ' + str(e), '11')

                elif cmd[:4] == 'RPAD':
                    # IPP2P:RND <> IPT:3000
                    # > “RPAD”[4B].SessionID[16B].Filemd5_i[32B].PartNum[8B]
                    # < “APAD”[4B].#Part[8B]

                    session_id = cmd[4:20]
                    md5 = cmd[20:52]
                    num_part = cmd[52:60]

                    self.print_trigger.emit(
                        "<= " + str(self.address[0]) + "  " + session_id + "  " + md5 + "  " + num_part, "10")
                    # Spazio
                    self.print_trigger.emit("", "10")

                    self.dbConnect.update_parts(md5, session_id, num_part)

                    response = "APAD" + num_part

                    try:
                        conn.sendall(response.encode("utf-8"))

                    except socket.error as msg:
                        self.print_trigger.emit('Socket Error: ' + str(response), '11')
                    except Exception as e:
                        self.print_trigger.emit('Error: ' + str(e), '11')

                    self.print_trigger.emit("Part " + str(num_part) + " succesfully downloaded by " + str(self.address[0]), "12")
                    # Spazio
                    self.print_trigger.emit("", "10")

                else:
                    self.print_trigger.emit("\nError: Command" + cmd + " not recognized", '11')

                try:
                    cmd = conn.recv(self.size).decode("utf-8")
                except socket.error:
                    pass
