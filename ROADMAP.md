# Lol-Manager Project Roadmap
## Complete Plan for Technical Success, Business Growth & AI Tools Mastery

**Last Updated:** 2025-12-15
**Project Vision:** Build a profitable OP.GG/U.GG alternative with AI-powered recommendations

---

## 📊 Current State Assessment

### ✅ What We Have
- Django backend with 7 well-structured database models
- Riot API client with rate limiting & retry logic
- Basic Champion/Item REST API endpoints
- Data sync from Riot Data Dragon API (172 champions, 398 items)
- PostgreSQL production database (Supabase) with verified data quality
- Comprehensive project documentation (README, CLAUDE.md, COMMITS.md)

### ❌ What's Missing
- **Frontend:** 0% (no React code)
- **Data Pipeline:** Player & match ingestion not integrated
- **Analytics Engine:** No stats aggregation or computation
- **Testing:** 0% coverage
- **Deployment:** No production setup
- **Monetization:** No revenue features

### 📈 Gap to OP.GG/U.GG
Currently at ~45% completion of target vision (Phases 1.1-1.4 complete - async infrastructure ready).

---

## 🎯 PHASE 1: Foundation & Data Pipeline (Weeks 1-4)
**Goal:** Get real League of Legends data flowing through the system

### 1.1 Fix Current Issues (Week 1, Days 1-2) ✅ COMPLETED 2025-12-21
- [x] Fix duplicate `description` field in Item model - RESOLVED: No duplicate exists (false positive)
- [x] Fix SummonerViewSet.get_queryset() signature - DONE (already fixed)
- [x] Fix Item field mappings (`builds_into` vs `build_into`) - DONE 2025-12-15
- [x] Add null handling in lol_update views - DONE 2025-12-15
- [x] Add PUUID unique constraint to Summoner model - RESOLVED: Already unique (primary_key=True)
- [x] Run migrations for all fixes - DONE 2025-12-15 (migrations 0012, 0013)
- [x] Fix Item/Rune ID field size (SmallInteger → Integer) - DONE 2025-12-15
- [x] Fix Item name field length (20 → 100 chars) - DONE 2025-12-15
- [x] Verify item data quality in production database - DONE 2025-12-15

### 1.2 Complete Database Schema (Week 1, Days 3-5) ✅ COMPLETED 2025-12-17
- [x] Add patch tracking:
  - `Patch` model (version, release_date, is_active) - DONE
  - Add patch_version foreign key to Match, ChampionStat - DONE
- [x] Enhance Match model:
  - Add `match_timestamp`, `queue_type` (IntegerField), `patch_version` - DONE
  - Add `region` field - DONE
  - Add `raw_data` JSONField for future reprocessing - DONE
- [x] Enhance MatchSummoners:
  - Add `role` and `lane` fields for position classification - DONE
  - Add `rune_ids` JSONField - DONE
  - Add `summoner_spell_ids` - DONE
- [x] Create aggregated stats models:
  - `ChampionRoleStats` (champion, role, patch, winrate, pickrate, banrate, games_played) - DONE
  - `BuildStats` (champion, role, patch, item_build, winrate, games_played) - DONE
  - `MatchupStats` (champion1, champion2, role, patch, winrate_diff, games_played) - DONE
- [x] Add database indexes:
  - Champion: name, id - DONE
  - Summoner: puuid, username, server - DONE
  - Match: match_timestamp, patch_version, queue_type - DONE
  - ChampionRoleStats: champion+role+patch composite - DONE
  - 30+ total indexes added for query optimization - DONE
- [x] Run makemigrations and migrate - DONE (migration 0014)

### 1.3 Integrate Riot API Data Ingestion (Week 2) ✅ COMPLETED 2025-12-19
- [x] Create `lol_update/services/` directory for business logic - DONE
- [x] Build `summoner_service.py`:
  - `fetch_summoner_by_riot_id(name, tag, region)` → saves to DB - DONE
  - `update_summoner_rank(puuid)` → updates ranked stats - DONE
- [x] Build `match_service.py`:
  - `fetch_match_history(puuid, count=20)` → gets match IDs - DONE
  - `fetch_match_details(match_id)` → saves Match + MatchSummoners - DONE
  - `fetch_match_timeline(match_id)` → extract role/lane from timeline - DONE
- [x] Build `static_data_service.py`:
  - `get_latest_version()` → dynamic version detection - DONE
  - `sync_champions(version)` → update champions for version - DONE
  - `sync_items(version)` → update items for version - DONE
  - `sync_runes(version)` → add rune data fetching - DONE
- [x] Add management commands:
  - `python3 manage.py fetch_summoner <name> <tag> --region=<region>` - DONE
  - `python3 manage.py sync_static_data` → champions, items, runes - DONE
  - `python3 manage.py fetch_matches <puuid> --count=<n>` - DONE
- [x] Test with real summoner account - DONE (tested with koldi#doggy)
- [x] Integrated RiotWatcher 3.3.1 for professional API handling - DONE
- [x] Created migration 0015 for PUUID field length - DONE

### 1.4 Background Task Queue (Week 3) ✅ COMPLETED 2025-12-21
- [x] Install Celery + Redis + Flower - DONE (Celery 5.4.0, Redis 5.0.1, Flower 2.0.1)
- [x] Configure Celery in `ChallengerBrain/celery.py` - DONE
- [x] Create async tasks (9 total) - DONE:
  - `fetch_summoner_task`, `update_summoner_rank_task`
  - `fetch_match_details_task`, `bulk_fetch_matches_task`
  - `sync_champions_task`, `sync_items_task`, `sync_runes_task`, `sync_all_static_data_task`
  - `update_tracked_summoners_ranks_task`
- [x] Set up periodic tasks - DONE:
  - Every 6 hours: `sync_all_static_data_task` (version-checked static data sync)
  - Hourly: `update_tracked_summoners_ranks_task` (batch of 50)
- [x] Version tracking system for Data Dragon - DONE (only sync on new versions)
- [x] Add task status tracking - DONE (django-celery-results for history)
- [x] Django admin integration - DONE (view task results + manage schedules)
- [x] Flower monitoring dashboard - DONE (web UI at :5555)
- [x] Retry logic for API errors - DONE (429 rate limits + 5xx errors)
- [x] Support local Redis + Upstash (production) - DONE
- [x] Database migrations applied - DONE (19 beat migrations, 11 results migrations)

### 1.5 Stats Computation Engine (Week 4)
- [ ] Create `lol_update/services/stats_engine.py`:
  - `compute_champion_role_stats(patch, role)` → aggregate winrate/pickrate
  - `compute_build_stats(champion, role, patch)` → most common builds + winrates
  - `compute_matchup_stats(role, patch)` → champion vs champion winrates
  - `compute_item_synergy(champion, patch)` → which items together have highest WR
- [ ] Create management command:
  - `python manage.py compute_stats --patch=14.23 --role=TOP`
  - `python manage.py compute_stats --all` → compute for all roles/patches
- [ ] Add sample size filtering (minimum 30 games for stats visibility)
- [ ] Test with real match data

**Deliverable:** Backend system that can fetch summoner data, matches, and compute aggregated statistics

---

## 🚀 PHASE 2: REST API Expansion (Weeks 5-6)
**Goal:** Build comprehensive API endpoints for frontend consumption

### 2.1 Player Profile Endpoints (Week 5, Days 1-3)
- [ ] `GET /api/summoner/{region}/{name}` → Summoner profile + rank
- [ ] `GET /api/summoner/{region}/{name}/matches?count=20&queue=RANKED_SOLO` → Match history
- [ ] `GET /api/summoner/{region}/{name}/champions?patch=latest` → Champion mastery + stats
- [ ] `GET /api/match/{match_id}` → Full match details with all players

### 2.2 Champion Stats Endpoints (Week 5, Days 4-5)
- [ ] `GET /api/champions?patch=latest&role=TOP` → Champion tier list
- [ ] `GET /api/champions/{champion_key}/stats?patch=latest&role=MID` → WR/PR/BR
- [ ] `GET /api/champions/{champion_key}/builds?role=JUNGLE&patch=latest` → Recommended builds
- [ ] `GET /api/champions/{champion_key}/matchups?role=TOP&patch=latest` → Counter picks
- [ ] `GET /api/champions/{champion_key}/runes?role=ADC&patch=latest` → Rune recommendations

### 2.3 Item & Meta Endpoints (Week 6)
- [ ] `GET /api/items?patch=latest&role=ADC` → Item statistics by role
- [ ] `GET /api/items/{item_id}/champions` → Which champions build this item
- [ ] `GET /api/meta/trends?patch=latest` → Patch meta overview (top champs by role)
- [ ] `GET /api/meta/builds?champion={key}&patch=latest` → Build diversity & winrates

### 2.4 API Documentation (Week 6, Days 4-5)
- [ ] Install drf-spectacular: `pip install drf-spectacular`
- [ ] Configure OpenAPI schema generation
- [ ] Add docstrings to all ViewSets and serializers
- [ ] Generate Swagger UI at `/api/docs/`
- [ ] Add example requests/responses
- [ ] Document rate limits and pagination

**Deliverable:** Comprehensive REST API that powers all frontend features

---
Deleted frontend from here, we are making it in another repo
---

## 🔧 PHASE 4: Infrastructure & Deployment (Weeks 13-14)
**Goal:** Deploy to production with proper DevOps practices

### 4.1 Backend Testing (Week 13, Days 1-2)
- [ ] Install pytest: `pip install pytest pytest-django pytest-cov`
- [ ] Create test fixtures for models (factories with `factory_boy`)
- [ ] Write unit tests:
  - Model tests (Champion, Summoner, Match creation)
  - Serializer tests (data validation)
  - API endpoint tests (response status, data shape)
  - Stats engine tests (aggregation correctness)
- [ ] Test Riot API client:
  - Mock API responses with `responses` library
  - Test rate limiting behavior
  - Test retry logic on failures
- [ ] Achieve >80% code coverage
- [ ] Set up GitHub Actions for CI:
  ```yaml
  # .github/workflows/django-tests.yml
  - Run tests on every push
  - Fail PR if tests don't pass
  ```

### 4.2 Database Migration to PostgreSQL (Week 13, Days 3-4)
- [ ] Set up Supabase project (already configured in settings)
- [ ] Update environment variables:
  - `DB_ENGINE=django.db.backends.postgresql`
  - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- [ ] Run migrations on PostgreSQL: `python manage.py migrate`
- [ ] Test all API endpoints against PostgreSQL
- [ ] Set up database backups (Supabase automatic backups)
- [ ] Create read replica for analytics queries (if needed)

### 4.3 Deployment Setup (Week 13, Day 5 - Week 14, Day 2)
- [ ] Backend deployment (Railway.app or Render.com):
  - Create `Procfile`: `web: gunicorn ChallengerBrain.wsgi`
  - Install gunicorn: `pip install gunicorn`
  - Set environment variables in hosting platform
  - Configure ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS
  - Deploy Django app
- [ ] Frontend deployment (Vercel or Netlify):
  - Build React app: `npm run build`
  - Configure environment variables (API_URL)
  - Set up automatic deployments from GitHub
- [ ] Redis deployment for Celery (Upstash or Railway):
  - Configure CELERY_BROKER_URL
- [ ] Celery worker deployment:
  - Separate worker dyno/service: `celery -A ChallengerBrain worker`
  - Celery beat scheduler: `celery -A ChallengerBrain beat`

### 4.4 Performance & Monitoring (Week 14, Days 3-5)
- [ ] Add Django Debug Toolbar for development profiling
- [ ] Optimize database queries:
  - Add `select_related()` and `prefetch_related()` to reduce N+1 queries
  - Add database indexes (already planned in Phase 1)
- [ ] Set up caching:
  - Install Redis cache backend: `pip install django-redis`
  - Cache API responses for 5 minutes
  - Cache aggregated stats for 1 hour
- [ ] Set up monitoring:
  - Install Sentry: `pip install sentry-sdk`
  - Configure error tracking
  - Set up performance monitoring
- [ ] Add logging:
  - Log all Riot API calls (rate limit hits, errors)
  - Log stats computation time
  - Log slow database queries (>100ms)
- [ ] Set up uptime monitoring (UptimeRobot or Better Uptime)

**Deliverable:** Production-ready deployment with monitoring, caching, and CI/CD

---

## 💰 PHASE 5: Monetization & Business Features (Weeks 15-18)
**Goal:** Make the platform profitable

### 5.1 User Accounts & Authentication (Week 15)
- [ ] Install django-allauth: `pip install django-allauth`
- [ ] Set up user registration/login:
  - Email/password authentication
  - Google OAuth login
  - Discord OAuth (League community uses Discord)
- [ ] Create user profile model:
  - Favorite champions
  - Saved summoners (track multiple accounts)
  - Preferred region
- [ ] Add JWT authentication for frontend:
  - `pip install djangorestframework-simplejwt`
  - Token refresh mechanism
- [ ] Frontend login/register pages

### 5.2 Premium Features (Week 16)
- [ ] Create `Subscription` model:
  - User, plan (FREE/PRO/PREMIUM), start_date, end_date
  - Payment status, Stripe customer_id
- [ ] Define free vs premium features:
  - **Free:**
    - Basic summoner lookup
    - Last 20 matches
    - Champion tier lists
    - Basic builds
  - **PRO ($4.99/month):**
    - Match history up to 100 games
    - Advanced filtering (by champion, date, outcome)
    - Detailed matchup statistics
    - Build diversity analysis
    - No ads
  - **PREMIUM ($9.99/month):**
    - All PRO features
    - Live game analysis (see teammates' stats in champ select)
    - Personal coaching insights (AI-powered recommendations)
    - Track unlimited summoners
    - API access (100 req/hour)
- [ ] Integrate Stripe payment:
  - `pip install stripe`
  - Create checkout page
  - Webhook for subscription events (created, canceled, renewed)
  - Cancel/downgrade flows
- [ ] Add subscription checks to API endpoints:
  - Return 402 Payment Required for premium endpoints
  - Throttle free users more aggressively

### 5.3 Ads Integration (Week 17, Days 1-2)
- [ ] Sign up for Google AdSense
- [ ] Add ad slots in frontend:
  - Banner ad above match history
  - Sidebar ad on champion pages
  - Interstitial ad after 5 page views (for free users)
- [ ] Ensure ads don't show for premium subscribers
- [ ] Expected revenue: $0.50-$2 RPM (Revenue Per 1000 impressions)

### 5.4 Affiliate Marketing (Week 17, Days 3-5)
- [ ] Partner with LoL-related services:
  - Skill-capped (coaching service) - 30% commission
  - ProGuides (educational content) - 20-30% commission
  - LoL merchandise stores
- [ ] Add referral links:
  - "Improve Your Gameplay" banner → Skill-capped
  - Champion build pages → "Watch Pro Guides"
- [ ] Track conversions with UTM parameters

### 5.5 Analytics & Growth (Week 18)
- [ ] Install Google Analytics 4 in frontend
- [ ] Track key metrics:
  - Daily Active Users (DAU)
  - Conversion rate (free → premium)
  - Retention (D1, D7, D30)
  - Most searched summoners/champions
  - Average session duration
- [ ] Set up conversion funnels:
  - Homepage → Search → Profile → Premium Signup
- [ ] A/B testing setup:
  - Test different premium pricing ($4.99 vs $7.99)
  - Test free trial (7 days vs 14 days)
- [ ] Email marketing:
  - Install django-anymail for transactional emails
  - Welcome email on signup
  - Weekly digest: "Your most played champion's meta this week"
  - Re-engagement campaign for inactive users

**Deliverable:** Monetized platform with subscriptions, ads, and affiliate revenue streams

---

## 🤖 PHASE 6: AI Assistant Feature (Weeks 19-22)
**Goal:** Differentiate from OP.GG/U.GG with AI-powered coaching

### 6.1 AI Architecture Planning (Week 19, Days 1-2)
- [ ] Choose AI approach:
  - **Option A:** Fine-tune GPT-4 on League of Legends data
  - **Option B:** RAG (Retrieval-Augmented Generation) with your aggregated stats
  - **Recommendation:** Option B (lower cost, more transparent)
- [ ] Define AI assistant capabilities:
  - Champion recommendations based on team comp
  - Build suggestions based on enemy team
  - Explain why a player is losing (low CS, poor itemization, bad matchups)
  - Personalized coaching tips based on match history

### 6.2 RAG System Implementation (Week 19-20)
- [ ] Set up vector database:
  - Install Pinecone or Weaviate: `pip install pinecone-client`
  - Store embeddings of champion stats, builds, matchups
- [ ] Create embeddings:
  - Use OpenAI embeddings API or open-source model (e.g., sentence-transformers)
  - Embed champion descriptions, builds, matchup summaries
- [ ] Build prompt system:
  - System prompt: "You are a League of Legends coach. Use only the provided stats to answer."
  - User query: "Why am I losing on Yasuo?"
  - Retrieved context: Yasuo's WR, user's KDA, common mistakes
  - LLM response: "Your CS/min is 5.2, but Yasuo needs 6.5+ to scale. Focus on farming."
- [ ] API endpoint:
  - `POST /api/ai/coach` with parameters: `summoner_puuid`, `question`
  - Returns AI response + citations (patch, sample size)

### 6.3 AI Features in Frontend (Week 21)
- [ ] Add AI coach chat interface:
  - Floating chat bubble on player profile page
  - Ask questions: "What should I build against tanks?"
  - Show response with references to stats
- [ ] Pre-built AI insights:
  - "Performance Analysis" section on profile
  - AI-generated summary: "You have 65% WR on assassins but 42% on tanks. Focus on your strengths."
- [ ] Live game analysis (premium feature):
  - Input teammates' summoner names
  - AI suggests: "Your jungler mains Lee Sin (68% WR). Consider playing champions with CC to synergize."

### 6.4 AI Quality & Safety (Week 22)
- [ ] Add fact-checking:
  - Cross-reference AI claims with database
  - Flag hallucinations (e.g., "This champion has 95% WR" when it's 51%)
- [ ] Rate limiting:
  - Free users: 3 AI questions per day
  - PRO users: 20 questions per day
  - PREMIUM users: Unlimited
- [ ] User feedback loop:
  - "Was this helpful?" thumbs up/down
  - Store feedback for model improvement
- [ ] Cost optimization:
  - Cache common questions (e.g., "Best Yasuo build")
  - Use cheaper models for simple queries (GPT-3.5-turbo)
  - Use GPT-4 only for complex coaching questions

**Deliverable:** AI-powered coaching assistant that provides personalized recommendations

---

## 📊 AI TOOLS MASTERY ROADMAP
**Goal:** Learn cutting-edge AI tools to accelerate development & reduce costs

### Level 1: Code Assistants (Week 1-2)
**Tool: GitHub Copilot**
- [ ] Install in VS Code: `GitHub Copilot` extension
- [ ] Practice:
  - Write function signatures, let Copilot complete
  - Use inline comments to guide code generation: `# Fetch summoner from Riot API and save to database`
  - Accept suggestions with Tab, cycle with Alt+]
- [ ] Advanced techniques:
  - Generate tests: Comment `# Test that Champion model saves correctly`
  - Refactor: Highlight code, ask Copilot Chat to simplify
- **Time saved:** 30-40% on boilerplate code

**Tool: Cursor (Alternative to VS Code)**
- [ ] Download Cursor IDE (cursor.sh)
- [ ] Features over Copilot:
  - Cmd+K: Edit code with AI instructions ("Add error handling")
  - Cmd+L: Chat with codebase context
  - Multi-file edits at once
- [ ] Practice:
  - Select a Django view, Cmd+K: "Add pagination to this endpoint"
  - Cmd+L: "Where are matches saved to the database?"
- **When to use:** Complex refactoring, multi-file changes

**Tool: Claude Code (What you're using now!)**
- [ ] Already active - maximize usage:
  - Delegate entire features: "Build the match ingestion service"
  - Use for planning: "Create a database migration plan for role tracking"
  - Code review: "Review this function for security issues"
- **Best practices:**
  - Provide context files (CLAUDE.md, ROADMAP.md)
  - Ask for explanations: "Explain how this serializer works"
  - Iterate: "Now add error handling to the previous code"

### Level 2: AI-Powered Research & Documentation (Week 3)
**Tool: Perplexity AI**
- [ ] Use for technical research:
  - "How does Riot API rate limiting work in 2025?"
  - "Best practices for Django database indexing for analytics"
- [ ] Compare to ChatGPT:
  - Perplexity cites sources (good for factual accuracy)
  - ChatGPT better for creative tasks
- **Use cases:** Architecture decisions, debugging obscure errors

**Tool: Notion AI**
- [ ] Set up project workspace in Notion
- [ ] Use AI for documentation:
  - Auto-generate API docs from endpoint descriptions
  - Summarize long meeting notes
  - Create task lists from brainstorm sessions
- [ ] Practice:
  - Write rough feature spec → Ask Notion AI to "Make this more professional"

**Tool: Gamma (AI Presentation Maker)**
- [ ] Create pitch deck for investors:
  - Input: "Pitch deck for League of Legends stats platform"
  - AI generates 10-slide deck with visuals
- [ ] Use for:
  - Investor pitches
  - Team onboarding docs
  - Feature announcements

### Level 3: Design & Content Creation (Week 4)
**Tool: Midjourney / DALL-E 3**
- [ ] Generate marketing visuals:
  - "Dark fantasy themed website banner for League of Legends stats site"
  - "Logo for ChallengerBrain - brain + challenger rank emblem"
- [ ] Use for:
  - Social media posts
  - Blog post headers
  - UI mockups (rough concepts)
- **Limitation:** Cannot generate exact UI components (use Figma AI for that)

**Tool: Figma AI (UI Design)**
- [ ] Install Figma + AI plugins:
  - "Autoflow" - auto-connect design elements
  - "Similayer" - select similar layers at once
- [ ] Generate UI components:
  - Describe: "Player profile card with rank badge, WR, and KDA stats"
  - Plugin generates component
- [ ] Practice:
  - Design champion tier list table
  - AI generates spacing, colors, responsive breakpoints

**Tool: Copy.ai / Jasper (Content Writing)**
- [ ] Generate marketing copy:
  - Landing page hero text: "Dominate the Rift with data-driven insights"
  - Email campaigns for premium signup
  - Blog post intros about meta shifts
- [ ] SEO optimization:
  - Input keyword: "Best Yasuo build 14.23"
  - AI generates SEO-optimized article outline

### Level 4: AI-Powered Marketing & Growth (Week 5)
**Tool: ChatGPT with Plugins (Web Browsing + Code Interpreter)**
- [ ] Market research:
  - "Analyze OP.GG's traffic trends in 2024-2025"
  - "What are the top complaints about U.GG on Reddit?"
- [ ] Competitor analysis:
  - "Compare feature sets: OP.GG vs U.GG vs Mobalytics"
- [ ] Data analysis:
  - Upload CSV of user signups → Ask for insights
  - "Which champions do premium users search most?"

**Tool: HubSpot AI (Marketing Automation)**
- [ ] Set up email campaigns:
  - AI writes subject lines (A/B tested)
  - Personalized email content based on user behavior
- [ ] Chatbot on website:
  - "Answer common questions about premium features"
- **ROI:** 2-3x conversion rate improvement

**Tool: Durable AI (No-Code Website Builder)**
- [ ] Generate landing page in 30 seconds:
  - Input: Business name, description
  - Output: Full website with copy, images, CTA buttons
- [ ] Use for:
  - Quick marketing pages (seasonal events)
  - A/B testing different value propositions
- **When to use:** Rapid prototyping, marketing campaigns

### Level 5: Advanced AI Engineering (Week 6-7)
**Tool: LangChain (AI App Framework)**
- [ ] Install: `pip install langchain openai`
- [ ] Build AI chains:
  - Chain 1: Retrieve player stats from database
  - Chain 2: Format stats as context for LLM
  - Chain 3: Generate coaching advice
- [ ] Practice:
  - Create "Champion Recommender" chain
  - Input: Enemy team comp
  - Output: Top 3 counter picks with reasoning

**Tool: LlamaIndex (RAG Framework)**
- [ ] Install: `pip install llama-index`
- [ ] Index your documentation:
  - Champion descriptions, patch notes, meta analysis
- [ ] Query interface:
  - "What changed for Yasuo in patch 14.23?"
  - AI retrieves patch notes + explains impact
- **Use case:** Power the AI coaching assistant in Phase 6

**Tool: AutoGPT / BabyAGI (Autonomous Agents)**
- [ ] Experiment with autonomous task completion:
  - Goal: "Research and summarize the top 5 League meta shifts in 2024"
  - Agent autonomously searches, reads, summarizes
- **Warning:** Not production-ready yet (use for research tasks only)

**Tool: Fine-Tuning GPT-4 / Claude**
- [ ] Create training dataset:
  - Collect 1000+ Q&A pairs: "Q: Best Yasuo build? A: <build> because..."
- [ ] Fine-tune model via OpenAI API
- [ ] Benefits:
  - More accurate responses
  - Lower cost per query (fine-tuned 3.5 cheaper than GPT-4)
- **When to use:** After reaching 10k+ users (data justifies cost)

### Level 6: AI DevOps & Monitoring (Week 8)
**Tool: Helicone (LLM Observability)**
- [ ] Install: Wraps OpenAI API calls
- [ ] Track:
  - Cost per user query
  - Latency (response time)
  - Error rates
- [ ] Alerts:
  - Notify if AI cost exceeds $100/day
  - Alert on high hallucination rate

**Tool: Weights & Biases (ML Experiment Tracking)**
- [ ] Track fine-tuning experiments:
  - Compare different prompts
  - Log accuracy metrics
- [ ] Visualize:
  - Cost vs accuracy tradeoffs
  - User satisfaction scores over time

**Tool: Promptfoo (Prompt Testing)**
- [ ] Test prompt variations:
  - Prompt A: "You are a League coach"
  - Prompt B: "You are a Challenger-ranked coach"
  - Compare which gets better user ratings
- [ ] Automated testing:
  - Run 100 test queries
  - Measure: accuracy, cost, speed

---

## 📈 SUCCESS METRICS & TIMELINE

### Technical Milestones
- **Month 1 (Phases 1-2):** Backend complete with data pipeline + API
- **Month 3 (Phase 3):** Frontend launched with core features
- **Month 4 (Phase 4):** Production deployment with monitoring
- **Month 5 (Phase 5):** Monetization live
- **Month 6 (Phase 6):** AI assistant feature launched

### Business Metrics (6-month targets)
- **Users:**
  - Month 1: 100 beta users
  - Month 3: 1,000 active users
  - Month 6: 10,000 active users
- **Revenue:**
  - Month 4: $500/month (ads)
  - Month 5: $2,000/month (ads + 50 PRO subs)
  - Month 6: $5,000/month (ads + 200 PRO + 50 PREMIUM subs)
- **Conversion Rate:**
  - Target: 2-3% free → PRO conversion
  - Target: 10% PRO → PREMIUM conversion

### AI Tools Proficiency
- **Week 4:** Competent with code assistants (30% productivity boost)
- **Week 8:** Proficient in design/content tools (can create marketing assets)
- **Month 3:** Advanced AI engineering (can build RAG systems)
- **Month 6:** Expert-level (can fine-tune models, run autonomous agents)

---

## 🚨 RISKS & MITIGATION

### Technical Risks
1. **Riot API Rate Limits**
   - Mitigation: Aggressive caching, queue system, contact Riot for higher limits
2. **Database Performance (100k+ users)**
   - Mitigation: Read replicas, materialized views, query optimization
3. **AI Hallucinations**
   - Mitigation: Fact-checking layer, cite sources, user feedback

### Business Risks
1. **Competition (OP.GG, U.GG are huge)**
   - Mitigation: Differentiate with AI coaching, better UX, niche focus (e.g., Chinese server stats)
2. **Low Conversion Rates**
   - Mitigation: A/B test pricing, offer free trial, optimize paywall placement
3. **Riot API Terms of Service**
   - Mitigation: Review ToS carefully, don't scrape, use official API only

### AI Tool Risks
1. **Over-reliance on AI (Code Quality)**
   - Mitigation: Code review, testing, understand what AI generates
2. **AI Costs Spiral**
   - Mitigation: Set budget alerts, use cheaper models, cache responses
3. **Prompt Injection Attacks**
   - Mitigation: Input sanitization, prompt firewalls, rate limiting

---

## 💡 IMMEDIATE NEXT STEPS (This Week)

1. **Fix Database Issues (Day 1)**
   - [ ] Run the fixes from Phase 1.1
   - [ ] Verify migrations work

2. **Set Up Development Environment (Day 2)**
   - [ ] Install GitHub Copilot in your IDE
   - [ ] Create Supabase account and configure database
   - [ ] Set up Redis for caching

3. **Get First Real Data (Day 3)**
   - [ ] Fetch your own summoner account
   - [ ] Pull your last 20 matches
   - [ ] Verify data appears in database

4. **Start Learning AI Tools (Days 4-5)**
   - [ ] Complete Copilot tutorials
   - [ ] Use ChatGPT to explain complex code sections
   - [ ] Try Cursor for refactoring one Django view

5. **Plan Week 2 (Day 5)**
   - [ ] Review this roadmap
   - [ ] Prioritize features (maybe skip some, add others)
   - [ ] Set up weekly check-ins to track progress

---

## 📚 RESOURCES

### Learning Resources
- **Django + DRF:** [testdriven.io](https://testdriven.io)
- **React:** [react.dev](https://react.dev)
- **Riot API:** [developer.riotgames.com](https://developer.riotgames.com)
- **AI Engineering:** [LangChain docs](https://python.langchain.com)
- **Growth:** [lennysnewsletter.com](https://lennysnewsletter.com)

### Tools & Platforms
- **Hosting:** Railway.app, Render.com, Vercel
- **Database:** Supabase (PostgreSQL)
- **AI:** OpenAI API, Claude API
- **Payments:** Stripe
- **Analytics:** Google Analytics 4, Mixpanel

### Community
- **Reddit:** r/leagueoflegends, r/summonerschool
- **Discord:** Join League dev communities
- **Twitter:** Follow @RiotSupport, @LoLEsports for API updates

---

## ✅ CONCLUSION

This roadmap is ambitious but achievable in 6 months with focused effort. The key differentiators for success:

1. **Speed:** Launch MVP in 3 months (faster than competitors)
2. **AI Advantage:** Coaching assistant that OP.GG doesn't have
3. **Better UX:** Cleaner design, faster load times
4. **Niche Focus:** Maybe start with one region (NA/EUW) before expanding

**Remember:** Don't try to build everything at once. Follow the phases sequentially. Each phase builds on the previous one.

Good luck, and may you reach Challenger in both coding and League! 🚀

---

**Last Updated:** 2025-12-15
**Next Review:** Weekly progress check-ins recommended

---

## 📝 Recent Progress

### 2025-12-21 - Phase 1.4 COMPLETE
- ✅ **Phase 1.4 COMPLETE** - Background Task Queue with Celery + Redis + Flower
- ✅ Installed Celery 5.4.0, Redis 5.0.1, Flower 2.0.1, django-celery-beat 2.8.1, django-celery-results 2.5.1
- ✅ Created 9 async tasks wrapping existing service functions (~466 lines)
- ✅ Configured periodic tasks: daily static data sync, hourly rank updates
- ✅ Django admin integration for task monitoring and schedule management
- ✅ Flower dashboard for real-time task visualization
- ✅ Retry logic for Riot API errors (429 rate limits, 5xx server errors)
- ✅ Support for local Redis (dev) and Upstash (production via env vars)
- ✅ Applied 30 database migrations (19 beat, 11 results)
- ✅ Updated CLAUDE.md with complete Celery documentation
- 🎯 **Progress Update:** Phases 1.1, 1.2, 1.3, 1.4 now 100% complete (40% → 45% overall)
- 🎯 **Next: Phase 1.5** - Stats Computation Engine

### 2025-12-21 - Phase 1.1 COMPLETE
- ✅ **Phase 1.1 COMPLETE** - All technical issues resolved
- ✅ Verified `description` field in Item model (no duplicate exists - false positive)
- ✅ Verified SummonerViewSet.get_queryset() already fixed (uses fresh queryset)
- ✅ Verified PUUID unique constraint exists (primary_key=True ensures uniqueness)
- 🎯 **Status Update:** Phases 1.1, 1.2, and 1.3 are now 100% complete
- 🎯 **Next: Phase 1.4** - Background Task Queue (Celery + Redis)

### 2025-12-19 - Phase 1.3 COMPLETE
- ✅ **Phase 1.3 COMPLETE** - Riot API data ingestion service layer fully implemented
- ✅ Created 4 production-ready service modules (~1,000 lines):
  - `riot_api_client.py` - RiotWatcher integration with region mapping
  - `summoner_service.py` - Player profile and ranked stats fetching
  - `match_service.py` - Match history and details with raw JSON storage
  - `static_data_service.py` - Champions, items, and runes sync from Data Dragon
- ✅ Created 3 Django management commands for easy data operations
- ✅ Integrated RiotWatcher 3.3.1 for automatic rate limiting and retry logic
- ✅ Created migration 0015: Increased PUUID field to support full Riot IDs
- ✅ Successfully tested with real Riot API data (koldi#doggy, 3 matches fetched)
- ✅ Fixed requirements.txt encoding (UTF-16 → UTF-8)
- ✅ Created comprehensive documentation (PHASE_1_3_COMPLETE.md, services/README.md)
- ✅ Set up git post-commit hook for commit documentation reminders
- ✅ Created custom `/pr` slash command for Pull Request creation
- ✅ Created Pull Request #3 for Phase 1.3 (develop → main)
- 🎯 **Next: Phase 1.4** - Background Task Queue (Celery + Redis)

### 2025-12-17 - Phase 1.2 COMPLETE
- ✅ **Phase 1.2 COMPLETE** - Database schema fully prepared for match ingestion and analytics
- ✅ Created 4 new models: Patch, ChampionRoleStats, BuildStats, MatchupStats
- ✅ Enhanced Match, MatchSummoners, ChampionStat with critical fields
- ✅ Added 30+ performance indexes for fast queries
- ✅ Migrated to production database (Supabase) - migration 0014
- ✅ Reorganized commit documentation into individual .md files
- ✅ Database now has: 11 tables, 172 champions, 398 items
