STABLE_DEBT_TOKEN_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "user",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "currentBalance",
                "type": "uint256"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "balanceIncrease",
                "type": "uint256"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "avgStableRate",
                "type": "uint256"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "newTotalSupply",
                "type": "uint256"
            }
        ],
        "name": "Burn",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "underlyingAsset",
                "type": "address"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "pool",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "incentivesController",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint8",
                "name": "debtTokenDecimals",
                "type": "uint8"
            },
            {
                "indexed": False,
                "internalType": "string",
                "name": "debtTokenName",
                "type": "string"
            },
            {
                "indexed": False,
                "internalType": "string",
                "name": "debtTokenSymbol",
                "type": "string"
            },
            {
                "indexed": False,
                "internalType": "bytes",
                "name": "params",
                "type": "bytes"
            }
        ],
        "name": "Initialized",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "user",
                "type": "address"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "onBehalfOf",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "currentBalance",
                "type": "uint256"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "balanceIncrease",
                "type": "uint256"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "newRate",
                "type": "uint256"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "avgStableRate",
                "type": "uint256"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "newTotalSupply",
                "type": "uint256"
            }
        ],
        "name": "Mint",
        "type": "event"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "user",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256"
            }
        ],
        "name": "burn",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getAverageStableRate",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getIncentivesController",
        "outputs": [
            {
                "internalType": "contract IAaveIncentivesController",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getSupplyData",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            },
            {
                "internalType": "uint40",
                "name": "",
                "type": "uint40"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getTotalSupplyAndAvgRate",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getTotalSupplyLastUpdated",
        "outputs": [
            {
                "internalType": "uint40",
                "name": "",
                "type": "uint40"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "user",
                "type": "address"
            }
        ],
        "name": "getUserLastUpdated",
        "outputs": [
            {
                "internalType": "uint40",
                "name": "",
                "type": "uint40"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "user",
                "type": "address"
            }
        ],
        "name": "getUserStableRate",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "contract ILendingPool",
                "name": "pool",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "underlyingAsset",
                "type": "address"
            },
            {
                "internalType": "contract IAaveIncentivesController",
                "name": "incentivesController",
                "type": "address"
            },
            {
                "internalType": "uint8",
                "name": "debtTokenDecimals",
                "type": "uint8"
            },
            {
                "internalType": "string",
                "name": "debtTokenName",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "debtTokenSymbol",
                "type": "string"
            },
            {
                "internalType": "bytes",
                "name": "params",
                "type": "bytes"
            }
        ],
        "name": "initialize",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "user",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "onBehalfOf",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "rate",
                "type": "uint256"
            }
        ],
        "name": "mint",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "user",
                "type": "address"
            }
        ],
        "name": "principalBalanceOf",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]
