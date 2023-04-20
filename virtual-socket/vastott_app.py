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
    try:
        soketti.bind((palvelin, portti))
    except:
        soketti.close()
        lopeta()
        
    print('Palvelin valmiina portissa {}.'.format(portti))
    print('Paina Ctrl-C lopettaaksesi.')
    puskurin_koko = 256  # Sama kuin ohjevideossa.
    while True:
        try:
            saapunut, _ = soketti.recvfrom(puskurin_koko)
            saapunut = saapunut.decode(encoding='utf8', errors='ignore')
                                      # 'ignore' on dekoodausongelmien varalta.
                                      # Oletusarvona olisi 'strict'.
            print(saapunut)

        except KeyboardInterrupt:  # Käyttäjä painoi Ctrl-C.
            break
        except:
            lopeta()
        
    soketti.close()
    input('\n------------' +\
          '\nSoketti suljettu.' +\
          '\nPaina Enter.')


main()    
