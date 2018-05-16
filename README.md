# BitTorrent

Il sistema a parti parallele è analogo al meccanismo a directory centralizzata in quanto ogni peer ha la necessità di comunicare al tracker le parti che mette a disposizione, aggiornandone periodicamente lo stato. Ogni peer può mettere a disposizione nuovi file ma si vincola a mettere a disposizione tutte le parti dei file che ha richiesto. Il download avviene richiedendo più parti in parallelo da differenti peer. La scelta dei peer da utilizzare per il download è effettuata dal peer ricevente, sulla base della conoscenza aggiornata delle parti possedute da ciascun peer, con un meccanismo che privilegia le parti meno presenti e che comunque sceglie a caso tra i peer a parità di priorità. I peer forniscono al tracker un aggiornamento periodico della situazione delle proprie parti e richiedono la situazione aggiornata delle parti relative ai file di cui stanno effettuando il download.

### Prerequisites

Nel file _config.py_ impostare proprio IPv4 e IPv6 e della directory a cui connettersi

### Running

Eseguire dal terminale:
```
 cd ../BitTorrent
 python3 main.py
```


## Authors :trollface:

* **ArtPes** - (https://github.com/ArtPes)
* **lovalova91** - (https://github.com/lovalova1991)
* **padovanl** - (https://github.com/padovanl)
* **lucia-rignanese** - (https://github.com/lucia-rignanese)

See also the list of [contributors](https://github.com/ArtPes/BitTorrent/graphs/contributors) who participated in this project.
