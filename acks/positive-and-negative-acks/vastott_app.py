#!/usr/bin/env python3

import luotettavuus as luotto
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
        # Varmistetaan, että virtuaalisoketin attribuutit ovat oikeanlaisia.
        soketti.tn_pudotus = 0
        soketti.tn_viive = 0
        soketti.tn_virhe = 0.7  # Vastaanottajan tapauksessa tämä vaikuttaa
                                # vastaanotettuihin paketteihin.
    
    except:
        lopeta()
    try:
        soketti.bind((palvelin, portti))
    except:
        soketti.close()
        lopeta()

    # Luodaan luotettavuuskerros-olio.
    puskurin_koko = 256  # Sama kuin ohjevideossa.
    luottokrs = luotto.Luottokerros(soketti, puskurin_koko)
        
    print('Palvelin valmiina portissa {}.'.format(portti))
    print('Paina Ctrl-C lopettaaksesi.')

    while True:
        try:
            saapunut = luottokrs.vastaanota()
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
