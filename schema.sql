-- schema.sql
-- This file defines the structure of our database table.

-- Delete the table if it already exists to ensure a clean start
DROP TABLE IF EXISTS games;

-- Create the main table to store our game sessions
CREATE TABLE games (
  id TEXT PRIMARY KEY,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  player1_name TEXT NOT NULL,
  player2_name TEXT,

  -- Columns for Match Tracking
  number_of_games INTEGER NOT NULL DEFAULT 1,
  wins_p1 INTEGER NOT NULL DEFAULT 0,
  wins_p2 INTEGER NOT NULL DEFAULT 0,

  -- The entire game object for the CURRENT round, stored as a JSON string
  game_state TEXT NOT NULL
);
