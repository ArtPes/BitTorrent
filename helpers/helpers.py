# coding=utf-8
import os
import hashlib
import random
import string
import sys
import time


def loop_menu(lock, header, options):
    action = None
    while action is None:
        output(lock, header)

        for idx, o in enumerate(options, start=1):
            output(lock, str(idx) + ": " + o + "")

        try:
            action = input()
        except SyntaxError:
            action = None

        if not action:
            output(lock, "Please select an option")
            action = None
        elif action == 'e':
            return None
        else:
            try:
                selected = int(action)
            except ValueError:
                output(lock, "A number is required")
                continue
            else:
                if selected > len(options):
                    output(lock, "Option " + str(selected) + " not available")
                    action = None
                    continue
                else:
                    return selected


def loop_int_input(lock, header):
    var = None
    while var is None:
        output(lock, header)

        try:
            var = input()
        except ValueError:
            var = None

        if not var:
            output(lock, "Type something!")
            var = None
        elif var == 'e':
            return None
        else:
            try:
                selected = int(var)
            except ValueError:
                output(lock, "A number is required")
                continue
            else:
                return selected


def loop_input(lock, header):
    var = None
    while var is None:
        output(lock, header)

        try:
            var = input()
        except ValueError:
            var = None

        if not var:
            output(lock, "Type something!")
            var = None
        elif var == 'e':
            return None
        else:
            return var


def hashfile(file, hasher, blocksize=65536):
    buf = file.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = file.read(blocksize)

    return hasher.hexdigest()


def hashfile_ip(file, hasher, bytes_ip):
    buf = file.read(65536)
    while len(buf) > 0:
        hasher.update(buf)
        buf = file.read(65536)

    hasher.update(bytes_ip)
    return hasher.hexdigest()


def get_shareable_files():
    files_list = []

    for root, dirs, files in os.walk("fileCondivisi"):
        for file in files:
            file_md5 = hashfile(open("fileCondivisi/" + file, 'rb'), hashlib.md5())
            files_list.append({
                'name': file,
                'md5': file_md5
            })

    return files_list


def id_generator(size, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def recvall(socket, chunk_size):
    """
    Legge dalla socket un certo numero di byte, evitando letture inferiori alla dimensione specificata

    :param socket: socket per le comunicazioni
    :type socket: object
    :param chunk_size: lunghezza (numero di byte) di una parte di file
    :type chunk_size: int
    :return: dati letti dalla socket
    :rtype: bytearray
    """

    data = socket.recv(chunk_size)  # Lettura di chunk_size byte dalla socket
    actual_length = len(data)

    # Se sono stati letti meno byte di chunk_size continua la lettura finchè non si raggiunge la dimensione specificata
    while actual_length < chunk_size:
        new_data = socket.recv(chunk_size - actual_length)
        actual_length += len(new_data)
        data += new_data

    return data


def filesize(self, n):
        """
        Calcola la dimensione del file

        :param n: nome del file
        :type n: str
        :return: dimensione del file
        :rtype: int
        """

        f = open(n, 'r')
        f.seek(0, 2)
        sz = f.tell()
        f.seek(0, 0)
        f.close()
        return sz


def output(lock, message):
    lock.acquire()
    print(message)
    lock.release()


def output_timer(lock, seconds):
    lock.acquire()

    for i in range(0, seconds):
        sys.stdout.write('\r%s' % i)
        sys.stdout.flush()
        time.sleep(1)

    lock.release()


def split_file(file, prefix, max_size, buffer=1024):
    chapters = 0
    uglybuf = ''
    with open(file, 'rb') as src:
        while True:
            tgt = open(prefix + '.%08d' % chapters, 'wb')
            written = 0
            while written < max_size:
                tgt.write(uglybuf)
                tgt.write(src.read(min(buffer, max_size - written)))
                written += min(buffer, max_size - written)
                uglybuf = src.read(1)
                if len(uglybuf) == 0:
                    break
            tgt.close()
            if len(uglybuf) == 0:
                break
            chapters += 1


def join_parts(infiles, outfile, buffer=1024):
    """
    infiles: a list of files
    outfile: the file that will be created
    buffer: buffer size in bytes
    """
    with open(outfile, 'w+b') as tgt:
        for infile in sorted(infiles):
            with open(infile, 'r+b') as src:
                while True:
                    data = src.read(buffer)
                    if data:
                        tgt.write(data)
                    else:
                        break
            os.remove(infile)


def join_parts_mac(infiles, outfile, buffer=1024):
    """
    infiles: a list of files
    outfile: the file that will be created
    buffer: buffer size in bytes
    """
    output = open(outfile, 'w+b')
    data = ""
    for infile in sorted(infiles):
        with open(infile, 'r+b') as src:
            while True:
                read = src.read(buffer)
                if read:
                    data += read
                else:
                    break
        os.remove(infile)

    output.write(data)
    output.close()