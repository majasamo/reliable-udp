#!/usr/bin/env python3

import socket as s
import virtsoketti as v
import sys


def lopeta():
    '''Tulostaa virheilmoituksen ja lopettaa ohjelman suorituksen.'''
    sys.exit('Virhe: {}.'.format(sys.exc_info()[1]))

    
def main():
    '''Pääohjelma.'''
    palvelin = 'localhost'
    portti = 9999
    osoiteperhe = s.AF_INET  # IPv4.
    sokettityyppi = s.SOCK_DGRAM  # UDP-soketti.

    try:
        # soketti = s.socket(osoiteperhe, sokettityyppi)
        soketti = v.Virtuaalisoketti(osoiteperhe, sokettityyppi)
    except:
        lopeta()
        
    print('Valmiina lähettämään.' +\
          '\nPaina Ctrl-C lopettaaksesi.')
    puskurin_koko = 256  # Sama kuin ohjevideossa.
    while True:
        try:
            lahteva = input('Anna lähetettävä teksti: ')
            lahteva = lahteva.encode('utf8')
            soketti.sendto(lahteva, (palvelin, portti))
        except KeyboardInterrupt:  # Käyttäjä painoi Ctrl-C.
            break
        except:
            lopeta()  # Jokin muu meni pieleen.
            
    soketti.close()
    input('\n------------' +\
          '\nSoketti suljettu.' +\
          '\nPaina Enter.')


main()    
