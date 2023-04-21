#!/usr/bin/env python3

import luotettavuus_lah as luotto
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
    vastott = (palvelin, portti)
    osoiteperhe = s.AF_INET  # IPv4.
    sokettityyppi = s.SOCK_DGRAM  # UDP-soketti.

    try:
        # soketti = s.socket(osoiteperhe, sokettityyppi)
        soketti = v.Virtuaalisoketti(osoiteperhe, sokettityyppi)
        # Varmistetaan, että virtuaalisoketin attribuutit ovat oikeanlaisia.
        soketti.tn_pudotus = .4
        soketti.tn_viive = .4
        soketti.tn_virhe = .3  
                               
    except:
        lopeta()

    # Luodaan luotettavuuskerros-olio.
    puskurin_koko = 256  # Sama kuin ohjevideossa.
    luottokrs = luotto.Luottolahettaja(soketti, puskurin_koko)
    luottokrs.aseta_alkutila()
        
    print('Valmiina lähettämään.' +\
          '\nPaina Ctrl-C lopettaaksesi.')
    while True:
        try:
            lahteva = input('Anna lähetettävä teksti: ')
            luottokrs.tilakone(lahteva, vastott)
        except KeyboardInterrupt:  # Käyttäjä painoi Ctrl-C.
            break
        except:
            lopeta()  # Jokin muu meni pieleen.
            
    soketti.close()
    input('\n------------' +\
          '\nSoketti suljettu.' +\
          '\nPaina Enter.')


main()    
