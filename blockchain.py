import hashlib
import json
from textwrap import dedent
from time import time
from urllib.parse import urlparse
from uuid import uuid4

from flask import Flask, jsonify, request

class Blockchain(object):
    def __init__(self):
        self.current_transactions = []
        self.chain = []
    
        #Creamos el bloque génesis
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        
        # Crea un nuevo bloque en la cadena
        # proof: <int> La prueba proporcionada por el algoritmo de prueba de trabajo
        # previous_hash: (opcional) <str> Hash del bloque previo
        # return: <dict> Nuevo bloque    
        
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or
        self.hash(self.chain[-1]),
        }
    #Reseteamos la lista actual de transacciones
        self.current_transactions = []
    
        self.chain.append(block)
        return block    
    
    def new_transaction(self, sender, recipient, amount):
        # Añade una nueva transacción para que vaya en el próximo bloque minado
        # sender: <str> Dirección del remitente
        # recipient: <str> Dirección del destinatario
        # amount: <int> Cantidad
        # return: <int> El índice del bloque en el que se insertará esta transacción
        
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1
    @property
        #Devuelve el último bloque en la cadena
    def last_block(self):
        return self.chain[-1]
    
    @staticmethod
    def hash(block):
        
        # Crea el hash SHA-256 de un bloque
        # block: <dict> Bloque
        # return: <str>

        # Debemos asegurarnos de que el diccionario está ordenado para evitar tener hashes inconsistentes
        block_string = json.dumps(block,
        sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof):
    
    # Algoritmo simple de prueba de trabajo:
    # - Encuentra un número p' de tal forma que hash(pp') contenga 4242, donde p es el p' previo.
    # - p es la prueba anterior y p' es la nueva prueba.
    # last_proof: <int>
    # return: <int>
        proof = 0
    
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
    
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
    
    # Valida la prueba: ¿hash(last_proof, proof) termina en 4242?
    # last_proof: <int> Prueba previa
    # proof: <int> Prueba actual
    # return: <bool> True si es correcto, Falso si no lo es
        
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        print(guess_hash)

        return guess_hash.endswith("4242")

#Generamos un nombre aleatorio para el nodo
app = Flask(__name__)

#Generamos una dirección única a nivel global para este nodo
node_identifier = str(uuid4()).replace('-', '')

#Blockchain
blockchain = Blockchain()

@app.route('/chain', methods=['GET']) #Devuelve la blockchain completa
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST']) #Subimos una nueva transacción
def new_transaction():
    values = request.get_json()

    #Comprobamos que los campos requeridos están en los datos enviados con POST
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Faltan valores', 400
    
    #Creamos una nueva transacción
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'La transacción se añadirá al bloque {index}'}
    return jsonify(response), 201

@app.route('/mine', methods=['GET']) #Minamos el bloque
def mine():
    #Ejecutamos el algoritmo de prueba de trabajo para conseguir la siguiente prueba
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    #Debemos recibir una recompensa por encontrar la prueba
    #El emisor es "0" para indicar que este nodo ha minado una moneda nueva
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    #Forjamos el nuevo bloque añadiéndolo a la cadena
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "Se ha forjado un nuevo bloque",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)