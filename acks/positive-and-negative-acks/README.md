Toteutus vastaa Kurose–Rossin rdt2.1-protokollaa. Sekvenssinumeroina
käytetään nollaa ja ykköstä ja kuittaukset (ACK ja NAK) lähetetään
tekstinä. Kuittauksen mukana on tarkistussumma mutta ei
sekvenssinumeroa. Jos vastaanottaja saa paketin, jossa on väärä
sekvenssinumero, se lähettää ACK-kuittauksen ja jää odottamaan
seuraavaa pakettia. Lähettäjä puolestaan uudelleenlähettää paketin
niin monta kertaa, että se saa ACK-kuittauksen, jossa ei ole
bittivirheitä.