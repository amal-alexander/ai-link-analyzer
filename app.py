import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from collections import defaultdict

# ==================================================
# DARK MODE FIX (Must be first Streamlit command after set_page_config)
# ==================================================
st.set_page_config(
    page_title="AI LinkAnalyzer Pro",
    page_icon="🔍",
    layout="wide"
)

st.markdown("""
<style>
    /* DARK MODE COMPATIBILITY */
    [data-testid="stAppViewContainer"] {
        background-color: var(--background-color) !important;
        color: var(--text-color) !important;
    }
    
    /* Dynamic color variables */
    :root {
        --background-color: #ffffff;
        --text-color: #000000;
        --secondary-color: #f0f2f6;
    }
    
    @media (prefers-color-scheme: dark) {
        :root {
            --background-color: #0e1117;
            --text-color: #ffffff;
            --secondary-color: #1a1a1a;
        }
        
        /* Fix input fields in dark mode */
        .stTextInput input, .stTextArea textarea, .stSelectbox select {
            color: #000000 !important;
            background-color: #ffffff !important;
        }
        
        /* Fix tables in dark mode */
        .stDataFrame {
            color: #000000 !important;
        }
    }
    
    /* YOUR EXISTING STYLES (now using CSS variables) */
    .header-style {
        font-size: 20px;
        font-weight: bold;
        color: var(--text-color);
        margin-bottom: 10px;
    }
    .subheader-style {
        font-size: 16px;
        font-weight: bold;
        color: #3498db; /* Keeping your blue color */
        margin-top: 15px;
    }
    .info-box {
        background-color: var(--secondary-color);
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 20px;
        color: var(--text-color);
    }
    .success-box {
        background-color: #e8f5e9;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 20px;
        color: #000000; /* Fixed success text color */
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px 24px;
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==================================================
# REST OF YOUR ORIGINAL CODE (EXACTLY AS IS)
# ==================================================
def is_same_domain(url, base):
    return urlparse(url).netloc == urlparse(base).netloc

def is_valid_internal_link(href, base_url):
    if not href:
        return False
    if href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
        return False
    absolute_url = urljoin(base_url, href)
    return is_same_domain(absolute_url, base_url)

def normalize_url(url):
    """Remove fragments and query parameters from URL"""
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

def is_in_nav_or_footer(element):
    for parent in element.parents:
        parent_classes = parent.get('class', []) or []
        parent_id = parent.get('id', '').lower()
        parent_role = parent.get('role', '').lower()
        
        # Navigation detection
        nav_indicators = {'nav', 'navbar', 'menu', 'navigation', 'header', 'main-menu'}
        if (parent.name in ['nav', 'header'] or
            any(x in parent_classes for x in nav_indicators) or
            any(x in parent_id for x in nav_indicators) or
            any(x in parent_role for x in {'navigation', 'menu'})):
            return True
        
        # Footer detection
        footer_indicators = {'footer', 'site-footer', 'bottom', 'copyright'}
        if (parent.name == 'footer' or
            any(x in parent_classes for x in footer_indicators) or
            any(x in parent_id for x in footer_indicators) or
            'contentinfo' in parent_role):
            return True
        
    return False

def get_anchor_name(a_tag):
    """Extract meaningful anchor name/identifier"""
    # First try to get the actual link text
    text = a_tag.get_text(' ', strip=True)
    if text and len(text) < 50:
        return text
    
    # Then try to find useful attributes
    for attr in ['title', 'aria-label', 'name', 'id']:
        if value := a_tag.get(attr):
            return f"{attr}: {value[:50]}"
    
    # Then check for image alt text
    if img := a_tag.find('img', alt=True):
        return f"Image: {img['alt'][:50]}"
    
    # Fallback to URL fragment
    if '#' in a_tag['href']:
        return f"Fragment: {a_tag['href'].split('#')[1][:50]}"
    
    return "Unnamed Anchor"

def crawl_page(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        return None, str(e)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    base_url = response.url
    url_groups = defaultdict(list)
    
    for a_tag in soup.find_all('a', href=True):
        if is_in_nav_or_footer(a_tag):
            continue
            
        href = a_tag['href'].strip()
        if not is_valid_internal_link(href, base_url):
            continue
            
        absolute_url = urljoin(base_url, href)
        normalized_url = normalize_url(absolute_url)
        anchor_name = get_anchor_name(a_tag)
        
        url_groups[normalized_url].append({
            'Anchor Name': anchor_name,
            'Full URL': absolute_url,
            'Normalized URL': normalized_url,
            'HTML Element': str(a_tag)[:200] + '...' if len(str(a_tag)) > 200 else str(a_tag)
        })
    
    return url_groups, None

# Header Section
st.title('🔍 AI LinkAnalyzer Pro')
st.markdown("""
<div class="info-box">
    <p>Analyze and group anchor links from any webpage while automatically excluding navigation and footer links.</p>
</div>
""", unsafe_allow_html=True)

# Input Section
with st.container():
    st.markdown('<div class="header-style">Enter Website URL</div>', unsafe_allow_html=True)
    url = st.text_input(
        "Website URL",
        placeholder="https://example.com",
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        analyze_btn = st.button("Analyze Links", type="primary")
    with col2:
        show_details = st.checkbox("Show detailed HTML elements", value=False)

# Results Section
if analyze_btn:
    if not url or not url.startswith(('http://', 'https://')):
        st.warning("⚠️ Please enter a valid URL starting with http:// or https://")
    else:
        with st.spinner("🔄 Analyzing webpage content..."):
            url_groups, error = crawl_page(url)
            
        if error:
            st.error(f"❌ Error: {error}")
        elif not url_groups:
            st.info("ℹ️ No anchor links found outside navigation/footer sections")
        else:
            # Prepare data for display
            all_anchors = []
            for dest_url, anchors in url_groups.items():
                for anchor in anchors:
                    all_anchors.append(anchor)
            
            total_anchors = len(all_anchors)
            unique_destinations = len(url_groups)
            
            # Success message
            st.markdown(f"""
            <div class="success-box">
                <h3>✅ Analysis Complete!</h3>
                <p>Found {total_anchors} anchor links grouped into {unique_destinations} unique destinations</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Sort destination URLs by number of links (descending)
            sorted_groups = sorted(url_groups.items(), key=lambda x: len(x[1]), reverse=True)
            
            # Display results in tabs
            tab1, tab2 = st.tabs(["📊 Grouped View", "📋 Flat View"])
            
            with tab1:
                st.markdown('<div class="subheader-style">Links Grouped by Destination</div>', unsafe_allow_html=True)
                for dest_url, anchors in sorted_groups:
                    with st.expander(f"🔗 {dest_url} ({len(anchors)} links)", expanded=True):
                        for anchor in anchors:
                            st.markdown(f"**{anchor['Anchor Name']}**")
                            st.write(f"Full URL: `{anchor['Full URL']}`")
                            if show_details:
                                st.code(anchor['HTML Element'], language='html')
                            st.write("---")
            
            with tab2:
                st.markdown('<div class="subheader-style">All Links</div>', unsafe_allow_html=True)
                # Sort flat view by destination URL with most links first
                flat_sorted = sorted(all_anchors, key=lambda x: -sum(1 for a in all_anchors if a['Normalized URL'] == x['Normalized URL']))
                for anchor in flat_sorted:
                    st.markdown(f"**{anchor['Anchor Name']}** → {anchor['Normalized URL']}")
                    st.write(f"Full URL: {anchor['Full URL']}")
                    if show_details:
                        st.code(anchor['HTML Element'], language='html')
                    st.write("---")

# Footer
st.markdown("---")
st.caption("""
<div style="text-align: center; color: #7f8c8d;">
    <p>AI LinkAnalyzer Pro v1.0 | Powered by Streamlit</p>
</div>
""", unsafe_allow_html=True)