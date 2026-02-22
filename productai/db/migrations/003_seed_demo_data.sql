-- Seed demo Plan and PRD so the app is never empty

INSERT OR IGNORE INTO plans (id, title, description, status, vision, target_audience, goals, success_metrics) VALUES (
    1,
    'HealthTrack Mobile App',
    'A comprehensive health and wellness tracking application for iOS and Android that helps users monitor daily habits, nutrition, exercise, and sleep patterns.',
    'active',
    'Empower individuals to take control of their health through intuitive daily tracking, personalized insights, and actionable recommendations — making healthy living simple and sustainable.',
    'Health-conscious adults aged 25-45 who want to improve their daily habits but find existing apps too complex or fragmented. Primary persona: busy professionals who want a single app for all wellness tracking.',
    '["Launch MVP with core tracking (nutrition, exercise, sleep) within 3 months", "Reach 10,000 active users in first quarter post-launch", "Achieve 4.5+ App Store rating", "60% weekly retention rate by month 6"]',
    '["Daily Active Users (DAU)", "Weekly retention rate", "Average session duration > 3 minutes", "NPS score > 50", "App Store rating >= 4.5"]'
);

INSERT OR IGNORE INTO prds (id, plan_id, title, status, overview, problem_statement, proposed_solution, content, timeline) VALUES (
    1,
    1,
    'HealthTrack — Daily Habit Tracker Feature',
    'review',
    'A habit tracking module within HealthTrack that lets users define, track, and visualize daily wellness habits with streak tracking and smart reminders.',
    'Users currently juggle multiple apps to track different health habits (water intake, meditation, steps, supplements). This fragmentation leads to low adherence — 67% of users abandon health apps within the first 2 weeks because the overhead of managing multiple tools is too high.',
    'Build an integrated habit tracker within HealthTrack that supports custom habits, provides streak-based motivation, sends intelligent reminders based on user patterns, and visualizes progress through intuitive charts.',
    '# Daily Habit Tracker — PRD

## Overview
A habit tracking module within HealthTrack that lets users define, track, and visualize daily wellness habits with streak tracking and smart reminders.

## User Stories

1. **As a user**, I want to create custom daily habits (e.g., "Drink 8 glasses of water") so that I can track what matters to me.
2. **As a user**, I want to check off habits throughout the day so that I can see my progress in real-time.
3. **As a user**, I want to see my current streak for each habit so that I feel motivated to maintain consistency.
4. **As a user**, I want smart reminders based on my typical schedule so that I don''t forget my habits.
5. **As a user**, I want to see weekly/monthly progress charts so that I can understand my long-term trends.

## Functional Requirements

- FR-1: Users can create up to 20 custom habits with name, icon, frequency, and target
- FR-2: One-tap check-off with undo support (30-second window)
- FR-3: Streak counter with longest-streak and current-streak tracking
- FR-4: Push notification reminders with smart scheduling (learns from user behavior)
- FR-5: Dashboard showing today''s habits with completion percentage
- FR-6: Weekly and monthly progress views with bar charts
- FR-7: Habit archival (soft delete) to preserve historical data

## Non-Functional Requirements

- NFR-1: Habit check-off must respond within 200ms
- NFR-2: Offline support — all tracking works without internet, syncs when reconnected
- NFR-3: Data encrypted at rest (AES-256) and in transit (TLS 1.3)
- NFR-4: Support for 100K concurrent users at launch

## Success Metrics

- 70% of active users create at least 3 habits in first week
- Average streak length > 7 days by month 3
- Habit completion rate > 65% across all users
- Feature contributes to 20% increase in daily session time',
    'Phase 1 (Weeks 1-4): Core habit CRUD + daily tracking UI. Phase 2 (Weeks 5-7): Streak engine + progress charts. Phase 3 (Weeks 8-9): Smart reminders + polish. Phase 4 (Week 10): Beta testing + launch.'
);
