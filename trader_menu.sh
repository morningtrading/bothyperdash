#!/bin/bash
# Trader Analysis Menu
# Interactive script for scraping and analyzing Hyperliquid traders

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Output directory (default: ~/Dropbox/_CURRENT, can be changed in settings)
OUTPUT_DIR="${OUTPUT_DIR:-$HOME/Dropbox/_CURRENT}"
FRESH_WALLETS="${OUTPUT_DIR}/freshwallets.rtf"

# Default values
PAGES=10
MIN_SHARPE=1.5
MAX_DRAWDOWN=0.5
RATE_LIMIT=1.0

# Function to print colored output
print_header() {
    echo -e "${CYAN}================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Main menu
show_main_menu() {
    clear
    print_header "HYPERLIQUID TRADER ANALYSIS SUITE"
    echo ""
    echo "1) Scrape wallets from Hyperdash"
    echo "2) Scrape wallets from Coinglass"
    echo "3) Scrape wallets from CoinMarketMan"
    echo "4) Manual wallet input"
    echo "5) Analyze existing wallet library"
    echo "6) Full workflow (Scrape + Analyze)"
    echo "7) 🆕 Unified Multi-Source Scraper (All-in-One)"
    echo "8) Settings"
    echo "9) View results"
    echo "0) Exit"
    echo ""
    echo -e "${CYAN}Current Settings:${NC}"
    echo "  Pages to scrape: ${PAGES}"
    echo "  Min Sharpe: ${MIN_SHARPE}"
    echo "  Max Drawdown: ${MAX_DRAWDOWN}"
    echo "  Rate Limit: ${RATE_LIMIT}s"
    echo "  Output dir: ${OUTPUT_DIR}"
    echo ""
}

# Scrape from Hyperdash
scrape_hyperdash() {
    print_header "SCRAPE FROM HYPERDASH"
    echo ""
    read -p "Number of pages to scrape [${PAGES}]: " input_pages
    pages=${input_pages:-$PAGES}

    echo ""
    print_info "Scraping ${pages} pages from Hyperdash..."
    python3 script_scrap_wallet.py -s hyperdash -p ${pages}

    if [ $? -eq 0 ]; then
        print_success "Scraping completed successfully!"
    else
        print_error "Scraping failed!"
        return 1
    fi

    echo ""
    read -p "Press Enter to continue..."
}

# Scrape from Coinglass
scrape_coinglass() {
    print_header "SCRAPE FROM COINGLASS"
    echo ""
    read -p "Number of pages to scrape [${PAGES}]: " input_pages
    pages=${input_pages:-$PAGES}

    echo ""
    print_info "Scraping ${pages} pages from Coinglass..."
    python3 script_scrap_wallet.py -s coinglass -p ${pages}

    if [ $? -eq 0 ]; then
        print_success "Scraping completed successfully!"
    else
        print_error "Scraping failed!"
        return 1
    fi

    echo ""
    read -p "Press Enter to continue..."
}

# Scrape from CoinMarketMan
scrape_coinmarketman() {
    print_header "SCRAPE FROM COINMARKETMAN"
    echo ""
    print_info "Scraping Money Printer segment (+\$1M PNL traders)..."
    echo ""
    python3 script_scrap_wallet.py -s cmm

    if [ $? -eq 0 ]; then
        print_success "Scraping completed successfully!"
    else
        print_error "Scraping failed!"
        return 1
    fi

    echo ""
    read -p "Press Enter to continue..."
}

# Manual wallet input
manual_input() {
    print_header "MANUAL WALLET INPUT"
    echo ""
    echo "Enter wallet addresses (one per line, empty line to finish):"
    echo ""

    addresses=()
    while true; do
        read -p "Address: " addr
        if [ -z "$addr" ]; then
            break
        fi

        # Validate Ethereum address format
        if [[ $addr =~ ^0x[a-fA-F0-9]{40}$ ]]; then
            addresses+=("$addr")
            print_success "Added: $addr"
        else
            print_error "Invalid address format. Must be 0x followed by 40 hex characters."
        fi
    done

    if [ ${#addresses[@]} -eq 0 ]; then
        print_warning "No addresses added."
        read -p "Press Enter to continue..."
        return
    fi

    echo ""
    print_info "Adding ${#addresses[@]} addresses to library..."

    # Append to CSV
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S.%6N")
    for addr in "${addresses[@]}"; do
        echo "${addr},manual,${timestamp}" >> scrapped_wallet_library.csv
    done

    print_success "${#addresses[@]} addresses added to scrapped_wallet_library.csv"
    echo ""
    read -p "Press Enter to continue..."
}

# Analyze wallets
analyze_wallets() {
    print_header "ANALYZE WALLET LIBRARY"
    echo ""

    if [ ! -f "scrapped_wallet_library.csv" ]; then
        print_error "No wallet library found! Please scrape wallets first."
        echo ""
        read -p "Press Enter to continue..."
        return 1
    fi

    # Count wallets
    wallet_count=$(($(wc -l < scrapped_wallet_library.csv) - 1))
    print_info "Found ${wallet_count} wallets in library"
    echo ""

    read -p "Limit analysis to how many wallets? [all]: " limit
    read -p "Fetch current positions? [y/N]: " fetch_pos

    cmd="python3 script_portfolio.py --rate-limit ${RATE_LIMIT}"

    if [ ! -z "$limit" ]; then
        cmd="${cmd} --limit ${limit}"
    fi

    if [[ $fetch_pos =~ ^[Yy]$ ]]; then
        cmd="${cmd} --fetch-positions"
    fi

    echo ""
    print_info "Running analysis..."
    eval $cmd

    if [ $? -eq 0 ]; then
        print_success "Analysis completed successfully!"

        # Check if filtered results exist
        if [ -f "portfolio_analysis_filtered.csv" ]; then
            trader_count=$(($(wc -l < portfolio_analysis_filtered.csv) - 1))
            print_success "Found ${trader_count} top traders matching criteria"

            # Copy to Dropbox
            copy_to_dropbox
        fi
    else
        print_error "Analysis failed!"
    fi

    echo ""
    read -p "Press Enter to continue..."
}

# Copy results to Dropbox
copy_to_dropbox() {
    print_header "COPY RESULTS TO DROPBOX"
    echo ""

    if [ ! -f "portfolio_analysis_filtered.csv" ]; then
        print_error "No filtered results found!"
        return 1
    fi

    # Create output directory if it doesn't exist
    mkdir -p "${OUTPUT_DIR}"

    # Convert CSV to RTF format (simple table)
    {
        echo "{\\rtf1\\ansi\\deff0"
        echo "{\\fonttbl{\\f0\\fnil\\fcharset0 Courier New;}}"
        echo "\\viewkind4\\uc1\\pard\\lang1033\\f0\\fs20"
        echo ""
        echo "HYPERLIQUID TOP TRADERS\\line"
        echo "Generated: $(date)\\line"
        echo "\\line"

        # Read CSV and format
        while IFS=, read -r address sharpe drawdown winrate pnl trades age age_years; do
            if [ "$address" != "address" ]; then
                echo "Address: $address\\line"
                echo "Sharpe Ratio: $sharpe\\line"
                echo "Max Drawdown: $drawdown\\line"
                echo "Win Rate: $winrate\\line"
                echo "Cumulative PnL: $pnl\\line"
                echo "Total Trades: $trades\\line"
                echo "\\line"
            fi
        done < portfolio_analysis_filtered.csv

        echo "}"
    } > "${FRESH_WALLETS}"

    print_success "Results copied to: ${FRESH_WALLETS}"

    # Also copy CSV files
    cp portfolio_analysis_filtered.csv "${OUTPUT_DIR}/freshwallets_filtered.csv" 2>/dev/null
    cp portfolio_analysis_positions.csv "${OUTPUT_DIR}/freshwallets_positions.csv" 2>/dev/null
    cp portfolio_analysis.csv "${OUTPUT_DIR}/freshwallets_full.csv" 2>/dev/null

    print_success "CSV files also copied to: ${OUTPUT_DIR}/"
}

# Full workflow
full_workflow() {
    print_header "FULL WORKFLOW: SCRAPE + ANALYZE"
    echo ""
    echo "Select source:"
    echo "1) Hyperdash"
    echo "2) Coinglass"
    echo "3) CoinMarketMan (Money Printer)"
    echo "4) All sources"
    echo ""
    read -p "Choice [1]: " source_choice
    source_choice=${source_choice:-1}

    read -p "Number of pages to scrape [${PAGES}]: " input_pages
    pages=${input_pages:-$PAGES}

    echo ""
    print_info "Starting full workflow..."
    echo ""

    # Scrape
    if [ "$source_choice" == "1" ] || [ "$source_choice" == "4" ]; then
        print_info "Scraping from Hyperdash..."
        python3 script_scrap_wallet.py -s hyperdash -p ${pages}
    fi

    if [ "$source_choice" == "2" ] || [ "$source_choice" == "4" ]; then
        print_info "Scraping from Coinglass..."
        python3 script_scrap_wallet.py -s coinglass -p ${pages}
    fi

    if [ "$source_choice" == "3" ] || [ "$source_choice" == "4" ]; then
        print_info "Scraping from CoinMarketMan..."
        python3 script_scrap_wallet.py -s cmm
    fi

    echo ""
    print_info "Running analysis with position fetching..."
    python3 script_portfolio.py --fetch-positions --rate-limit ${RATE_LIMIT}

    if [ $? -eq 0 ]; then
        print_success "Full workflow completed!"
        copy_to_dropbox
    else
        print_error "Workflow failed during analysis!"
    fi

    echo ""
    read -p "Press Enter to continue..."
}

# Unified Multi-Source Scraper
unified_scraper() {
    print_header "UNIFIED MULTI-SOURCE SCRAPER"
    echo ""
    print_info "This will scrape all 3 sources, merge results, and rank by performance"
    echo ""
    echo "Options:"
    echo "1) Scrape all sources + Analyze (creates big_file.csv)"
    echo "2) Analyze existing scrapped_wallet_library.csv"
    echo ""
    read -p "Choice [1]: " mode_choice
    mode_choice=${mode_choice:-1}

    read -p "Number of pages per source [${PAGES}]: " input_pages
    pages=${input_pages:-$PAGES}

    echo ""
    
    if [ "$mode_choice" == "1" ]; then
        print_info "Starting unified scraper (scrape + analyze)..."
        python3 unified_scraper.py --scrape --analyze \
            --hyperdash-pages ${pages} \
            --coinglass-pages ${pages} \
            --include-cmm \
            --rate-limit ${RATE_LIMIT} \
            --min-sharpe ${MIN_SHARPE} \
            --max-drawdown ${MAX_DRAWDOWN} \
            --exclude-hyper-scrapers
    else
        print_info "Analyzing existing wallet library..."
        python3 unified_scraper.py --analyze \
            --rate-limit ${RATE_LIMIT} \
            --min-sharpe ${MIN_SHARPE} \
            --max-drawdown ${MAX_DRAWDOWN} \
            --exclude-hyper-scrapers
    fi

    if [ $? -eq 0 ]; then
        print_success "Unified scraper completed successfully!"
        echo ""
        print_info "Output files created:"
        echo "  - big_file.csv (all wallets with full data)"
        echo "  - big_file_ranked.csv (top performers ranked)"
        echo ""
        
        # Copy to Dropbox if directory exists
        if [ -d "${OUTPUT_DIR}" ]; then
            print_info "Copying results to ${OUTPUT_DIR}..."
            cp big_file.csv "${OUTPUT_DIR}/big_file.csv" 2>/dev/null
            cp big_file_ranked.csv "${OUTPUT_DIR}/big_file_ranked.csv" 2>/dev/null
            print_success "Results copied to output directory"
        fi
    else
        print_error "Unified scraper failed!"
    fi

    echo ""
    read -p "Press Enter to continue..."
}

# Settings menu
settings_menu() {
    while true; do
        clear
        print_header "SETTINGS"
        echo ""
        echo "1) Pages to scrape: ${PAGES}"
        echo "2) Min Sharpe ratio: ${MIN_SHARPE}"
        echo "3) Max Drawdown: ${MAX_DRAWDOWN}"
        echo "4) API Rate limit: ${RATE_LIMIT}s"
        echo "5) Output directory: ${OUTPUT_DIR}"
        echo "0) Back to main menu"
        echo ""
        read -p "Choice: " choice

        case $choice in
            1)
                read -p "Enter pages to scrape: " PAGES
                ;;
            2)
                read -p "Enter min Sharpe ratio: " MIN_SHARPE
                ;;
            3)
                read -p "Enter max drawdown (0.0-1.0): " MAX_DRAWDOWN
                ;;
            4)
                read -p "Enter API rate limit (seconds): " RATE_LIMIT
                ;;
            5)
                read -p "Enter output directory path: " OUTPUT_DIR
                FRESH_WALLETS="${OUTPUT_DIR}/freshwallets.rtf"
                print_success "Output directory updated to: ${OUTPUT_DIR}"
                sleep 1
                ;;
            0)
                break
                ;;
            *)
                print_error "Invalid choice"
                sleep 1
                ;;
        esac
    done
}

# View results
view_results() {
    clear
    print_header "VIEW RESULTS"
    echo ""

    if [ -f "portfolio_analysis_filtered.csv" ]; then
        trader_count=$(($(wc -l < portfolio_analysis_filtered.csv) - 1))
        echo -e "${GREEN}Top Traders (${trader_count} found):${NC}"
        echo ""
        cat portfolio_analysis_filtered.csv | head -11 | column -t -s,
        echo ""

        if [ $trader_count -gt 10 ]; then
            print_info "Showing first 10 of ${trader_count} traders"
        fi
    else
        print_warning "No results found. Run analysis first."
    fi

    echo ""

    if [ -f "portfolio_analysis_positions.csv" ]; then
        pos_count=$(($(wc -l < portfolio_analysis_positions.csv) - 1))
        echo -e "${GREEN}Current Positions (${pos_count} traders):${NC}"
        echo ""
        cat portfolio_analysis_positions.csv | head -6 | cut -d, -f1,2,4,5,8 | column -t -s,
        echo ""

        if [ $pos_count -gt 5 ]; then
            print_info "Showing first 5 of ${pos_count} traders with positions"
        fi
    fi

    echo ""
    read -p "Press Enter to continue..."
}

# Main loop
main() {
    while true; do
        show_main_menu
        read -p "Enter choice: " choice

        case $choice in
            1)
                scrape_hyperdash
                ;;
            2)
                scrape_coinglass
                ;;
            3)
                scrape_coinmarketman
                ;;
            4)
                manual_input
                ;;
            5)
                analyze_wallets
                ;;
            6)
                full_workflow
                ;;
            7)
                unified_scraper
                ;;
            8)
                settings_menu
                ;;
            9)
                view_results
                ;;
            0)
                print_info "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid choice"
                sleep 1
                ;;
        esac
    done
}

# Run main
main
