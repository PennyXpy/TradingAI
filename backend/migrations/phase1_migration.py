#!/usr/bin/env python3
"""
Phase 1 Database Migration Script
=================================

This script migrates the existing TradingAI database to the Phase 1 enhanced schema.
It preserves all existing data while adding new tables and relationships.

Migration Steps:
1. Backup existing database
2. Create new Phase 1 tables
3. Migrate existing data to new schema
4. Create indexes for performance
5. Validate migration success

Usage:
    python migrations/phase1_migration.py --backup --migrate --validate
    
Options:
    --backup: Create backup of existing database
    --migrate: Perform the migration
    --validate: Validate migration success
    --rollback: Rollback to backup (if migration fails)
"""

import argparse
import sqlite3
import shutil
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database paths
DB_PATH = Path("backend/models/tradingai.db")
BACKUP_PATH = Path(f"backend/models/tradingai_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")

class Phase1Migrator:
    """
    Handles migration from current schema to Phase 1 enhanced schema
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.backup_path = BACKUP_PATH
        self.conn = None
    
    def create_backup(self) -> bool:
        """
        Create backup of existing database
        """
        try:
            if self.db_path.exists():
                shutil.copy2(self.db_path, self.backup_path)
                logger.info(f"Database backed up to: {self.backup_path}")
                return True
            else:
                logger.warning("Database file does not exist, skipping backup")
                return True
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def disconnect(self):
        """Disconnect from database"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def execute_sql_file(self, sql_content: str):
        """Execute SQL statements from string"""
        try:
            cursor = self.conn.cursor()
            cursor.executescript(sql_content)
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to execute SQL: {e}")
            self.conn.rollback()
            return False
    
    def create_phase1_tables(self) -> bool:
        """
        Create Phase 1 tables with proper relationships
        """
        sql_statements = """
        -- Create enhanced users table (modify existing)
        CREATE TABLE IF NOT EXISTS users_new (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            preferences TEXT DEFAULT '{}'
        );
        
        -- Create user_sessions table (replaces usertoken)
        CREATE TABLE IF NOT EXISTS user_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users_new(id)
        );
        
        -- Create instruments table (master registry)
        CREATE TABLE IF NOT EXISTS instruments (
            id TEXT PRIMARY KEY,
            symbol TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('stock', 'etf', 'crypto')),
            sector TEXT,
            market_cap REAL,
            exchange TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create user_followings table (enhanced following system)
        CREATE TABLE IF NOT EXISTS user_followings (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            instrument_id TEXT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            alert_enabled BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (user_id) REFERENCES users_new(id),
            FOREIGN KEY (instrument_id) REFERENCES instruments(id),
            UNIQUE(user_id, instrument_id)
        );
        
        -- Create news_articles table
        CREATE TABLE IF NOT EXISTS news_articles (
            id TEXT PRIMARY KEY,
            headline TEXT NOT NULL,
            content TEXT,
            source TEXT NOT NULL,
            author TEXT,
            published_at TIMESTAMP NOT NULL,
            sentiment_score REAL,
            symbols TEXT DEFAULT '[]',
            url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create news_cache table (for efficient news-instrument mapping)
        CREATE TABLE IF NOT EXISTS news_cache (
            id TEXT PRIMARY KEY,
            instrument_id TEXT NOT NULL,
            article_id TEXT NOT NULL,
            relevance_score REAL DEFAULT 1.0,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (instrument_id) REFERENCES instruments(id),
            FOREIGN KEY (article_id) REFERENCES news_articles(id)
        );
        
        -- Create earning_reports table
        CREATE TABLE IF NOT EXISTS earning_reports (
            id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            quarter INTEGER NOT NULL,
            year INTEGER NOT NULL,
            summary TEXT,
            price_impact REAL,
            eps_actual REAL,
            eps_estimate REAL,
            revenue_actual REAL,
            revenue_estimate REAL,
            report_date TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create agent_contexts table
        CREATE TABLE IF NOT EXISTS agent_contexts (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            conversation_history TEXT DEFAULT '[]',
            last_analysis TEXT,
            agent_version TEXT DEFAULT '1.0',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users_new(id)
        );
        
        -- Create market_cache table
        CREATE TABLE IF NOT EXISTS market_cache (
            id TEXT PRIMARY KEY,
            instrument_id TEXT NOT NULL,
            data_type TEXT NOT NULL CHECK (data_type IN ('price', 'volume', 'technical', 'fundamentals')),
            data_json TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (instrument_id) REFERENCES instruments(id)
        );
        
        -- Create alerts table
        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            alert_type TEXT NOT NULL CHECK (alert_type IN ('price', 'news', 'earnings', 'volume')),
            message TEXT NOT NULL,
            triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            acknowledged BOOLEAN DEFAULT FALSE,
            acknowledged_at TIMESTAMP,
            alert_config TEXT DEFAULT '{}',
            FOREIGN KEY (user_id) REFERENCES users_new(id)
        );
        
        -- Update investments table to add user relationship
        CREATE TABLE IF NOT EXISTS investments_new (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            quantity REAL NOT NULL,
            price_per_unit REAL NOT NULL,
            transaction_date TIMESTAMP NOT NULL,
            transaction_type TEXT NOT NULL,
            source TEXT DEFAULT 'manual',
            fees REAL DEFAULT 0.0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users_new(id)
        );
        """
        
        logger.info("Creating Phase 1 tables...")
        return self.execute_sql_file(sql_statements)
    
    def migrate_existing_data(self) -> bool:
        """
        Migrate data from existing tables to new schema
        """
        try:
            cursor = self.conn.cursor()
            
            # Migrate users table
            logger.info("Migrating users...")
            cursor.execute("""
                INSERT OR IGNORE INTO users_new (id, username, email, hashed_password, is_active, created_at)
                SELECT id, username, email, hashed_password, is_active, created_at
                FROM user
            """)
            
            # Migrate usertoken to user_sessions
            logger.info("Migrating user tokens to sessions...")
            cursor.execute("""
                INSERT OR IGNORE INTO user_sessions (id, user_id, token, expires_at, created_at)
                SELECT id, user_id, token, expires_at, created_at
                FROM usertoken
            """)
            
            # Create instruments from existing followed and investment data
            logger.info("Creating instruments from existing data...")
            
            # Get unique symbols from followed table
            cursor.execute("SELECT DISTINCT symbol, asset_type FROM followed")
            followed_symbols = cursor.fetchall()
            
            # Get unique symbols from investments table  
            cursor.execute("SELECT DISTINCT symbol, asset_type FROM investment")
            investment_symbols = cursor.fetchall()
            
            # Combine and deduplicate symbols
            all_symbols = {}
            for row in followed_symbols:
                all_symbols[row[0]] = row[1]
            for row in investment_symbols:
                all_symbols[row[0]] = row[1]
            
            # Insert instruments
            for symbol, asset_type in all_symbols.items():
                instrument_id = f"inst_{symbol}_{asset_type}"
                cursor.execute("""
                    INSERT OR IGNORE INTO instruments (id, symbol, name, type)
                    VALUES (?, ?, ?, ?)
                """, (instrument_id, symbol, symbol, asset_type))
            
            # Migrate followed to user_followings
            logger.info("Migrating followed assets...")
            cursor.execute("""
                INSERT OR IGNORE INTO user_followings (id, user_id, instrument_id, added_at)
                SELECT 
                    f.id,
                    f.user_id,
                    'inst_' || f.symbol || '_' || f.asset_type,
                    f.added_at
                FROM followed f
            """)
            
            # Migrate investments
            logger.info("Migrating investments...")
            cursor.execute("""
                INSERT OR IGNORE INTO investments_new 
                SELECT * FROM investment
            """)
            
            self.conn.commit()
            logger.info("Data migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate data: {e}")
            self.conn.rollback()
            return False
    
    def create_indexes(self) -> bool:
        """
        Create indexes for optimal performance
        """
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users_new(email);",
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users_new(username);",
            "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(token);",
            "CREATE INDEX IF NOT EXISTS idx_instruments_symbol ON instruments(symbol);",
            "CREATE INDEX IF NOT EXISTS idx_instruments_type ON instruments(type);",
            "CREATE INDEX IF NOT EXISTS idx_followings_user_id ON user_followings(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_followings_instrument_id ON user_followings(instrument_id);",
            "CREATE INDEX IF NOT EXISTS idx_news_published_at ON news_articles(published_at);",
            "CREATE INDEX IF NOT EXISTS idx_news_cache_instrument ON news_cache(instrument_id);",
            "CREATE INDEX IF NOT EXISTS idx_earnings_symbol ON earning_reports(symbol);",
            "CREATE INDEX IF NOT EXISTS idx_earnings_date ON earning_reports(report_date);",
            "CREATE INDEX IF NOT EXISTS idx_market_cache_instrument ON market_cache(instrument_id);",
            "CREATE INDEX IF NOT EXISTS idx_market_cache_expires ON market_cache(expires_at);",
            "CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON alerts(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_alerts_symbol ON alerts(symbol);",
            "CREATE INDEX IF NOT EXISTS idx_investments_user_id ON investments_new(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_investments_symbol ON investments_new(symbol);"
        ]
        
        try:
            cursor = self.conn.cursor()
            for index_sql in indexes:
                cursor.execute(index_sql)
            self.conn.commit()
            logger.info("Indexes created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            return False
    
    def finalize_migration(self) -> bool:
        """
        Finalize migration by replacing old tables with new ones
        """
        try:
            cursor = self.conn.cursor()
            
            # Rename old tables as backup
            old_tables = ["user", "usertoken", "followed", "investment"]
            for table in old_tables:
                cursor.execute(f"ALTER TABLE {table} RENAME TO {table}_backup;")
            
            # Rename new tables to final names
            cursor.execute("ALTER TABLE users_new RENAME TO user;")
            cursor.execute("ALTER TABLE investments_new RENAME TO investment;")
            
            self.conn.commit()
            logger.info("Migration finalized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to finalize migration: {e}")
            self.conn.rollback()
            return False
    
    def validate_migration(self) -> bool:
        """
        Validate that migration completed successfully
        """
        try:
            cursor = self.conn.cursor()
            
            # Check table counts
            validations = [
                ("user", "users_backup"),
                ("user_sessions", "usertoken_backup"),
                ("user_followings", "followed_backup"),
                ("investment", "investment_backup")
            ]
            
            for new_table, old_table in validations:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {new_table}")
                    new_count = cursor.fetchone()[0]
                    
                    cursor.execute(f"SELECT COUNT(*) FROM {old_table}")
                    old_count = cursor.fetchone()[0]
                    
                    if new_count < old_count:
                        logger.error(f"Data loss detected: {new_table} has {new_count} rows, {old_table} had {old_count} rows")
                        return False
                    else:
                        logger.info(f"✓ {new_table}: {new_count} rows migrated from {old_table}: {old_count} rows")
                except sqlite3.OperationalError as e:
                    logger.warning(f"Could not validate {new_table} vs {old_table}: {e}")
            
            # Check new tables exist
            new_tables = [
                "instruments", "news_articles", "news_cache", "earning_reports",
                "agent_contexts", "market_cache", "alerts"
            ]
            
            for table in new_tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
                if not cursor.fetchone():
                    logger.error(f"New table {table} was not created")
                    return False
                else:
                    logger.info(f"✓ New table {table} created successfully")
            
            logger.info("Migration validation passed!")
            return True
            
        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            return False
    
    def rollback(self) -> bool:
        """
        Rollback migration by restoring from backup
        """
        try:
            if self.backup_path.exists():
                shutil.copy2(self.backup_path, self.db_path)
                logger.info(f"Database rolled back from: {self.backup_path}")
                return True
            else:
                logger.error("No backup file found for rollback")
                return False
        except Exception as e:
            logger.error(f"Failed to rollback: {e}")
            return False
    
    def run_migration(self, with_backup: bool = True, validate: bool = True) -> bool:
        """
        Run complete migration process
        """
        logger.info("Starting Phase 1 database migration...")
        
        # Step 1: Backup
        if with_backup and not self.create_backup():
            logger.error("Backup failed, aborting migration")
            return False
        
        # Step 2: Connect to database
        try:
            self.connect()
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
        
        # Step 3: Create new tables
        if not self.create_phase1_tables():
            logger.error("Failed to create Phase 1 tables")
            self.disconnect()
            return False
        
        # Step 4: Migrate data
        if not self.migrate_existing_data():
            logger.error("Failed to migrate existing data")
            self.disconnect()
            return False
        
        # Step 5: Create indexes
        if not self.create_indexes():
            logger.error("Failed to create indexes")
            self.disconnect()
            return False
        
        # Step 6: Finalize migration
        if not self.finalize_migration():
            logger.error("Failed to finalize migration")
            self.disconnect()
            return False
        
        # Step 7: Validate
        if validate and not self.validate_migration():
            logger.error("Migration validation failed")
            self.disconnect()
            return False
        
        self.disconnect()
        logger.info("Phase 1 migration completed successfully! 🎉")
        return True

def main():
    parser = argparse.ArgumentParser(description="Phase 1 Database Migration")
    parser.add_argument("--backup", action="store_true", help="Create backup before migration")
    parser.add_argument("--migrate", action="store_true", help="Perform migration")
    parser.add_argument("--validate", action="store_true", help="Validate migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback to backup")
    parser.add_argument("--db-path", help="Database file path")
    
    args = parser.parse_args()
    
    migrator = Phase1Migrator(args.db_path)
    
    if args.rollback:
        success = migrator.rollback()
        return 0 if success else 1
    
    if args.migrate:
        success = migrator.run_migration(
            with_backup=args.backup,
            validate=args.validate
        )
        return 0 if success else 1
    
    if args.backup:
        success = migrator.create_backup()
        return 0 if success else 1
    
    if args.validate:
        migrator.connect()
        success = migrator.validate_migration()
        migrator.disconnect()
        return 0 if success else 1
    
    # Default: run full migration
    success = migrator.run_migration()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())