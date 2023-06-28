import json
VE_HELPER = json.loads('''
[
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "_voting_escrow",
          "type": "address"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "constructor"
    },
    {
      "inputs": [
        {
          "internalType": "uint256[]",
          "name": "tokenIds",
          "type": "uint256[]"
        }
      ],
      "name": "getveNFTInfo",
      "outputs": [
        {
          "components": [
            {
              "internalType": "address",
              "name": "owner",
              "type": "address"
            },
            {
              "internalType": "int128",
              "name": "rewardAmount",
              "type": "int128"
            },
            {
              "internalType": "int128",
              "name": "amount",
              "type": "int128"
            },
            {
              "internalType": "uint256",
              "name": "end",
              "type": "uint256"
            },
            {
              "internalType": "address",
              "name": "token",
              "type": "address"
            },
            {
              "internalType": "int128",
              "name": "baseAmount",
              "type": "int128"
            }
          ],
          "internalType": "struct TokenInformation[]",
          "name": "",
          "type": "tuple[]"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "voting_escrow",
      "outputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    }
  ]
''')