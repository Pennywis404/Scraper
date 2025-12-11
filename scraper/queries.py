"""GraphQL queries for Product Hunt API."""

# Fragment commun pour les champs d'un post
POST_FIELDS = """
    id
    name
    tagline
    description
    url
    website
    votesCount
    commentsCount
    createdAt
    featuredAt
    topics(first: 5) {
        nodes {
            name
        }
    }
    makers {
        name
        username
    }
"""

# Get today's posts
POSTS_TODAY = f"""
query PostsToday($first: Int!, $after: String) {{
    posts(first: $first, after: $after) {{
        pageInfo {{
            hasNextPage
            endCursor
        }}
        nodes {{
            {POST_FIELDS}
        }}
    }}
}}
"""

# Get posts from a specific date
POSTS_BY_DATE = f"""
query PostsByDate($postedAfter: DateTime!, $postedBefore: DateTime!, $first: Int!, $after: String) {{
    posts(postedAfter: $postedAfter, postedBefore: $postedBefore, first: $first, after: $after) {{
        pageInfo {{
            hasNextPage
            endCursor
        }}
        nodes {{
            {POST_FIELDS}
        }}
    }}
}}
"""
