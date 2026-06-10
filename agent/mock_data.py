SAFE = {
    "scenario_id": "safe",
    "feature": "Add dark mode toggle to user preferences panel",
    "decision": "GO",
    "risk_level": "LOW",
    "risk_score": 0.08,
    "blast_radius_pct": 4.2,
    "affected_services": [
        {
            "service_id": "SERVICE-FRONTEND-001",
            "service_name": "frontend-service",
            "fragility_score": 0.06,
            "incident_count_30d": 0,
            "error_rate_pct": 0.04,
            "slo_burn_rate": 0.01,
            "dependency_depth": 1,
            "health_status": "healthy",
            "last_incident": None,
            "dependencies": ["user-preferences-service"]
        },
        {
            "service_id": "SERVICE-PREFS-002",
            "service_name": "user-preferences-service",
            "fragility_score": 0.09,
            "incident_count_30d": 0,
            "error_rate_pct": 0.08,
            "slo_burn_rate": 0.02,
            "dependency_depth": 1,
            "health_status": "healthy",
            "last_incident": None,
            "dependencies": []
        }
    ],
    "deployment_strategy": "Standard full rollout",
    "reasoning": "Both affected services are completely healthy with zero incidents in the past 30 days. Error rates are negligible at under 0.1%. SLO budgets are fully intact. The dark mode toggle only touches the frontend rendering layer and user preferences storage — neither is a critical path. No risk factors identified. This deployment can proceed immediately at full traffic.",
    "top_risks": [
        "Minor CSS rendering inconsistencies on older browsers (very low probability)",
        "User preference sync delay on first toggle (cosmetic, non-blocking)",
        "None — no significant risks identified"
    ],
    "conditions": None,
    "topology_map": {
        "nodes": ["frontend-service", "user-preferences-service"],
        "edges": [("frontend-service", "user-preferences-service")]
    }
}

RISKY = {
    "scenario_id": "risky",
    "feature": "Integrate loyalty points rewards into the checkout flow",
    "decision": "GO_WITH_CONDITIONS",
    "risk_level": "HIGH",
    "risk_score": 0.61,
    "blast_radius_pct": 23.4,
    "affected_services": [
        {
            "service_id": "SERVICE-CHECKOUT-003",
            "service_name": "checkout-service",
            "fragility_score": 0.38,
            "incident_count_30d": 1,
            "error_rate_pct": 0.82,
            "slo_burn_rate": 0.14,
            "dependency_depth": 2,
            "health_status": "degraded",
            "last_incident": "2 weeks ago — 14min outage during peak traffic",
            "dependencies": ["payment-service", "loyalty-service", "order-management-service"]
        },
        {
            "service_id": "SERVICE-PAYMENT-004",
            "service_name": "payment-service",
            "fragility_score": 0.74,
            "incident_count_30d": 3,
            "error_rate_pct": 2.31,
            "slo_burn_rate": 0.67,
            "dependency_depth": 2,
            "health_status": "degraded",
            "last_incident": "3 days ago — payment gateway timeout spike",
            "dependencies": ["fraud-detection-service", "billing-service"]
        },
        {
            "service_id": "SERVICE-LOYALTY-005",
            "service_name": "loyalty-service",
            "fragility_score": 0.21,
            "incident_count_30d": 0,
            "error_rate_pct": 0.19,
            "slo_burn_rate": 0.04,
            "dependency_depth": 1,
            "health_status": "healthy",
            "last_incident": None,
            "dependencies": ["points-ledger-db"]
        },
        {
            "service_id": "SERVICE-ORDER-006",
            "service_name": "order-management-service",
            "fragility_score": 0.29,
            "incident_count_30d": 1,
            "error_rate_pct": 0.44,
            "slo_burn_rate": 0.09,
            "dependency_depth": 2,
            "health_status": "healthy",
            "last_incident": "3 weeks ago — brief DB connection pool exhaustion",
            "dependencies": ["payment-service", "inventory-service"]
        }
    ],
    "deployment_strategy": "Canary rollout — 5% traffic, off-peak window only",
    "reasoning": "The payment-service is the critical blocker. It has experienced 3 incidents in the last 30 days — most recently a payment gateway timeout spike just 3 days ago — and is currently burning its SLO error budget at 67% of the monthly allocation with only 18 days remaining. Deploying a new feature that adds loyalty-point writes to every checkout transaction will increase payment-service load by an estimated 15-20%. Given its current fragility score of 0.74, this creates meaningful probability of a cascading failure during peak traffic. The checkout-service is also in a mildly degraded state. Deployment is possible but only under controlled conditions.",
    "top_risks": [
        "payment-service (fragility 0.74): 3 incidents in 30 days, SLO burning at 67% — new checkout load may trigger another timeout cascade",
        "checkout-service (fragility 0.38): currently degraded, adding loyalty-write step increases transaction time by ~80ms at the 99th percentile",
        "Blast radius of 23.4%: a payment-service failure during checkout would affect nearly 1 in 4 active users"
    ],
    "conditions": [
        "Deploy between 02:00–05:00 UTC only (lowest traffic window)",
        "Start at 5% canary — do not expand until payment-service error rate stable for 30 consecutive minutes",
        "Set an automatic rollback trigger: if payment-service error rate exceeds 3% during rollout, revert immediately",
        "Do not deploy until payment-service SLO burn rate drops below 30% (currently 67%)"
    ],
    "topology_map": {
        "nodes": ["checkout-service", "payment-service", "loyalty-service",
                  "order-management-service", "fraud-detection-service",
                  "billing-service", "points-ledger-db", "inventory-service"],
        "edges": [
            ("checkout-service", "payment-service"),
            ("checkout-service", "loyalty-service"),
            ("checkout-service", "order-management-service"),
            ("payment-service", "fraud-detection-service"),
            ("payment-service", "billing-service"),
            ("loyalty-service", "points-ledger-db"),
            ("order-management-service", "payment-service"),
            ("order-management-service", "inventory-service")
        ]
    }
}

FATAL = {
    "scenario_id": "fatal",
    "feature": "Migrate authentication service to new OAuth2 provider",
    "decision": "NO_GO",
    "risk_level": "CRITICAL",
    "risk_score": 0.94,
    "blast_radius_pct": 89.1,
    "affected_services": [
        {
            "service_id": "SERVICE-AUTH-007",
            "service_name": "auth-service",
            "fragility_score": 0.96,
            "incident_count_30d": 7,
            "error_rate_pct": 8.73,
            "slo_burn_rate": 1.0,
            "dependency_depth": 3,
            "health_status": "critical",
            "last_incident": "ACTIVE RIGHT NOW — token validation failures since 14:32 UTC",
            "dependencies": ["session-manager", "user-service", "api-gateway"]
        },
        {
            "service_id": "SERVICE-GATEWAY-008",
            "service_name": "api-gateway",
            "fragility_score": 0.71,
            "incident_count_30d": 4,
            "error_rate_pct": 3.12,
            "slo_burn_rate": 0.88,
            "dependency_depth": 3,
            "health_status": "degraded",
            "last_incident": "Yesterday — 22min elevated 5xx rate",
            "dependencies": ["auth-service", "rate-limiter", "load-balancer"]
        },
        {
            "service_id": "SERVICE-SESSION-009",
            "service_name": "session-manager",
            "fragility_score": 0.52,
            "incident_count_30d": 2,
            "error_rate_pct": 1.87,
            "slo_burn_rate": 0.41,
            "dependency_depth": 2,
            "health_status": "degraded",
            "last_incident": "1 week ago — Redis connection pool exhaustion",
            "dependencies": ["auth-service", "cache-cluster"]
        },
        {
            "service_id": "SERVICE-USER-010",
            "service_name": "user-service",
            "fragility_score": 0.33,
            "incident_count_30d": 1,
            "error_rate_pct": 0.61,
            "slo_burn_rate": 0.12,
            "dependency_depth": 2,
            "health_status": "healthy",
            "last_incident": "2 weeks ago — brief DB query timeout",
            "dependencies": ["auth-service", "user-db"]
        },
        {
            "service_id": "SERVICE-FRONT-001",
            "service_name": "frontend-service",
            "fragility_score": 0.44,
            "incident_count_30d": 2,
            "error_rate_pct": 1.24,
            "slo_burn_rate": 0.31,
            "dependency_depth": 1,
            "health_status": "degraded",
            "last_incident": "5 days ago — elevated login failure rate caused by auth-service",
            "dependencies": ["auth-service", "api-gateway"]
        }
    ],
    "deployment_strategy": "HALT — do not deploy under any conditions",
    "reasoning": "HARD STOP. The auth-service has an ACTIVE incident right now — token validation failures have been occurring since 14:32 UTC and are not yet resolved. With an 8.73% error rate and a fragility score of 0.96, this is the most dangerous service in the entire topology. The SLO budget is completely exhausted (burn rate 1.0 — meaning 100% of the monthly budget is already gone). Deploying a migration of this service while it is actively failing would replace a struggling system with an untested one mid-incident, with a blast radius of 89.1% of all active users. The api-gateway is also degraded and directly depends on auth-service. This deployment must not proceed under any circumstances until: (1) the active incident is resolved, (2) auth-service maintains a stable error rate below 0.5% for a minimum of 48 continuous hours, and (3) a full rollback plan with tested execution is in place.",
    "top_risks": [
        "auth-service has an ACTIVE INCIDENT right now — deploying mid-incident would replace a broken system with an untested one simultaneously",
        "89.1% blast radius — an auth-service failure locks out nearly all users from the entire platform, not just one feature",
        "SLO budget fully exhausted — zero margin for any additional errors; this service is already in breach"
    ],
    "conditions": None,
    "topology_map": {
        "nodes": ["frontend-service", "api-gateway", "auth-service",
                  "session-manager", "user-service", "rate-limiter",
                  "cache-cluster", "user-db"],
        "edges": [
            ("frontend-service", "auth-service"),
            ("frontend-service", "api-gateway"),
            ("api-gateway", "auth-service"),
            ("api-gateway", "rate-limiter"),
            ("auth-service", "session-manager"),
            ("auth-service", "user-service"),
            ("session-manager", "cache-cluster"),
            ("user-service", "user-db")
        ]
    }
}

def get_scenario(feature_description: str) -> dict:
    feature_lower = feature_description.lower()
    
    safe_keywords = ["dark mode", "toggle", "theme", "preferences", "settings", "ui", "frontend", "color"]
    fatal_keywords = ["auth", "authentication", "login", "oauth", "sso", "identity", "password", "session", "token", "migrate auth"]
    
    if any(k in feature_lower for k in fatal_keywords):
        return FATAL
    if any(k in feature_lower for k in safe_keywords):
        return SAFE
        
    # Default to RISKY if no keywords match — it's the most interesting scenario
    return RISKY
