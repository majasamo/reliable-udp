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
    vastott = (palvelin, portti)
    osoiteperhe = s.AF_INET  # IPv4.
    sokettityyppi = s.SOCK_DGRAM  # UDP-soketti.

    try:
        # soketti = s.socket(osoiteperhe, sokettityyppi)
        soketti = v.Virtuaalisoketti(osoiteperhe, sokettityyppi)
        # Varmistetaan, että virtuaalisoketin attribuutit ovat oikeanlaisia.
        soketti.tn_pudotus = 0
        soketti.tn_viive = 0
        soketti.tn_virhe = 0.2  # Lähettäjän tapauksessa tämä vaikuttaa
                                # vastaanotettuihin kuittauksiin.
    except:
        lopeta()

    # Luodaan luotettavuuskerros-olio.
    puskurin_koko = 256  # Sama kuin ohjevideossa.
    luottokrs = luotto.Luottokerros(soketti, puskurin_koko)
        
    print('Valmiina lähettämään.' +\
          '\nPaina Ctrl-C lopettaaksesi.')
    while True:
        try:
            lahteva = input('Anna lähetettävä teksti: ')
            luottokrs.laheta_mjono(lahteva, vastott)
        except KeyboardInterrupt:  # Käyttäjä painoi Ctrl-C.
            break
        except:
            lopeta()  # Jokin muu meni pieleen.
            
    soketti.close()
    input('\n------------' +\
          '\nSoketti suljettu.' +\
          '\nPaina Enter.')


main()    
