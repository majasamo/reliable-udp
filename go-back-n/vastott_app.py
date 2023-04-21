#!/usr/bin/env python3

import luotettavuus_vastott as luotto
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
        # Virtuaalisoketin attribuuttien säätö.
        soketti.tn_pudotus = .0
        soketti.tn_viive = .0
        soketti.tn_virhe = .0
        soketti.viive_ala = 1
        soketti.viive_yla = 3
                             
    
    except:
        lopeta()
    try:
        soketti.bind((palvelin, portti))
    except:
        soketti.close()
        lopeta()

    # Luodaan luotettavuuskerros-olio.
    puskurin_koko = 256  # Sama kuin ohjevideossa.
    luottokrs = luotto.Luottovastaanottaja(soketti, puskurin_koko)
    
    print('Palvelin valmiina portissa {}.'.format(portti))
    print('Paina Ctrl-C lopettaaksesi.\n')

    # Lukusilmukka.
    while True:
        try:
            # Kysytään lähettäjältä tullutta viestiä ja tulostetaan
            # se, jos se ei ole None.
            saapunut = luottokrs.ota_vastaan()
            if saapunut:
                print('Saapunut viesti: "{}".\n'.format(saapunut))

        except KeyboardInterrupt:  # Käyttäjä painoi Ctrl-C.
            break
        except:
            lopeta()
        
    soketti.close()
    input('\n------------' +\
          '\nSoketti suljettu.' +\
          '\nPaina Enter.')


main()    
