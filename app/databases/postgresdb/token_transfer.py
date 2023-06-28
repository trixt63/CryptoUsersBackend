import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.decorators.postgres_item import postgres_items_to_json
from app.decorators.time_exe import sync_log_time_exe, TimeExeTag
from app.utils.logger_utils import get_logger
from config import PostgresDBConfig

logger = get_logger('TokenTransferDB')


class TokenTransferDB:
    def __init__(self):
        # Set up the database connection and create the table
        self._get_sessions(PostgresDBConfig.CONNECTION_URLS)

    @sync_log_time_exe(tag=TimeExeTag.database)
    def _get_sessions(self, connection_urls):
        self.sessions = {}
        for connection_url, chains in connection_urls.items():
            engine = create_engine(connection_url)
            session = sessionmaker(bind=engine)()
            for chain in chains:
                self.sessions[chain] = session

    def _get_session(self, chain_id):
        if chain_id not in self.sessions:
            raise ValueError(f'Chain {chain_id} not supported')
        return self.sessions[chain_id]

    def close(self):
        for chain, session in self.sessions.items():
            try:
                session.close()
            except Exception as ex:
                logger.exception(ex)

    ####################
    #      Query       #
    ####################

    @sync_log_time_exe(tag=TimeExeTag.database)
    @postgres_items_to_json
    def get_outgoing_token_amount(self, chain_id, wallet_address: str, from_block: int, to_block=None):
        block_number_filter = ''
        if from_block is not None:
            block_number_filter += f'AND block_number >= {from_block} '
        if to_block is not None:
            block_number_filter += f'AND block_number <= {to_block} '

        query = f"""
            SELECT contract_address, SUM(value) as total_value
            FROM chain_{chain_id}.{PostgresDBConfig.TRANSFER_EVENT_TABLE}
            WHERE from_address = '{wallet_address}'
            {block_number_filter}
            GROUP BY contract_address
        """
        session = self._get_session(chain_id)
        outgoing = session.execute(query).all()
        return outgoing

    @sync_log_time_exe(tag=TimeExeTag.database)
    @postgres_items_to_json
    def get_incoming_token_amount(self, chain_id, wallet_address: str, from_block: int, to_block=None):
        block_number_filter = ''
        if from_block is not None:
            block_number_filter += f'AND block_number >= {from_block} '
        if to_block is not None:
            block_number_filter += f'AND block_number <= {to_block} '

        query = f"""
            SELECT contract_address, SUM(value) as total_value
            FROM chain_{chain_id}.{PostgresDBConfig.TRANSFER_EVENT_TABLE}
            WHERE to_address = '{wallet_address}'
            {block_number_filter}
            GROUP BY contract_address
        """
        session = self._get_session(chain_id)
        incoming = session.execute(query).all()
        return incoming

    @sync_log_time_exe(tag=TimeExeTag.database)
    @postgres_items_to_json
    def get_event_transfer_by_transaction(self, chain_id, tx_hash):
        start_time = time.time()
        query = f"""
            SELECT * FROM chain_{chain_id}.{PostgresDBConfig.TRANSFER_EVENT_TABLE}
            WHERE transaction_hash = '{tx_hash}'
        """
        session = self._get_session(chain_id)
        event_transfer = session.execute(query).all()
        logger.info(f'Load data took {time.time() - start_time}')
        return event_transfer

    @sync_log_time_exe(tag=TimeExeTag.database)
    @postgres_items_to_json
    def get_event_transfer_by_contract(self, chain_id, contract_address, from_block=None, to_block=None, skip=0, limit=None):
        block_number_filter = ''
        if from_block is not None:
            block_number_filter += f'AND block_number >= {from_block} '
        if to_block is not None:
            block_number_filter += f'AND block_number <= {to_block} '

        query = f"""
            SELECT * FROM chain_{chain_id}.{PostgresDBConfig.TRANSFER_EVENT_TABLE}
            WHERE contract_address = '{contract_address}'
            {block_number_filter}
            ORDER BY block_number DESC
            OFFSET {skip} 
        """
        if limit is not None:
            query += f"LIMIT {limit}"

        session = self._get_session(chain_id)
        event_transfer = session.execute(query).all()
        return event_transfer

    @sync_log_time_exe(tag=TimeExeTag.database)
    @postgres_items_to_json
    def count_event_transfer_by_contract(self, chain_id, contract_address, from_block=None, to_block=None):
        block_number_filter = ''
        if from_block is not None:
            block_number_filter += f'AND block_number >= {from_block} '
        if to_block is not None:
            block_number_filter += f'AND block_number <= {to_block} '

        query = f"""
            SELECT COUNT(*) as number_of_events FROM chain_{chain_id}.{PostgresDBConfig.TRANSFER_EVENT_TABLE}
            WHERE contract_address = '{contract_address}'
            {block_number_filter}
        """
        session = self._get_session(chain_id)
        event_transfer = session.execute(query).all()
        return event_transfer
