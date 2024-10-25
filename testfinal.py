import streamlit as st
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine
import warnings

warnings.filterwarnings('ignore')

#for connecting to database
user = 'root' #TODO
password = 'Namikaze.549632' #TODO 
host = '127.0.0.1'  # e.g., 'localhost' or '127.0.0.1'
database = 'mco1_datawarehouse'
port = '3306'  # Default MySQL port
engine = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}')

# configure page 
st.set_page_config(page_title="Video Game Data", page_icon=":video_game:", layout="wide")
st.title("🎮 Video Game Data Dashboard")
st.markdown('<style> div.block-container{padding-top:2rem;}</style>', unsafe_allow_html=True)

#sections sidebar
st.sidebar.header("Choose data to view:")
data_view = st.sidebar.selectbox("Select a Data View", ["General Data", "Developer Data", "Genre Data", "Tag Data"])

genre_options_query = pd.read_sql("SELECT * FROM dimm_genre", engine)
release_date_query = pd.read_sql("SELECT DISTINCT year FROM dimm_date order by year", engine)
tag_options_query = pd.read_sql("SELECT name FROM dimm_tag", engine)
developer_options_query = pd.read_sql("SELECT name FROM dimm_developer", engine)

#General Section
if data_view == "General Data":
    st.header("📊 General Data Overview")
    
    # graphs
    st.subheader("Total Number of Games Released Over the Years")
    total_games_query = """
    SELECT YEAR(d.release_date) AS year, COUNT(fg.game_id) AS total_games
    FROM fact_game fg
    JOIN dimm_date d ON fg.date_id = d.date_id
    GROUP BY YEAR(d.release_date)
    ORDER BY YEAR(d.release_date);
    """
    total_games_df = pd.read_sql(total_games_query, engine)
    fig_total_games = px.line(total_games_df, x='year', y='total_games', title="Total Number of Games Released Over the Years")
    st.plotly_chart(fig_total_games)

    st.subheader("Average Game Price Over the Years")
    price_query = """
    SELECT YEAR(d.release_date) AS year, AVG(fg.price) AS avg_price
    FROM fact_game fg
    JOIN dimm_date d ON fg.date_id = d.date_id
    GROUP BY YEAR(d.release_date)
    ORDER BY YEAR(d.release_date);
    """
    price_df = pd.read_sql(price_query, engine)
    fig_price = px.line(price_df, x='year', y='avg_price', title='Average Game Price per Year')
    st.plotly_chart(fig_price)

    st.subheader("Total Peak CCU Over the Years")
    peak_ccu_query = """
    SELECT YEAR(d.release_date) AS year, SUM(fg.peak_ccu) AS total_peak_ccu
    FROM fact_game fg
    JOIN dimm_date d ON fg.date_id = d.date_id
    GROUP BY YEAR(d.release_date)
    ORDER BY YEAR(d.release_date);
    """
    peak_ccu_df = pd.read_sql(peak_ccu_query, engine)
    fig_peak_ccu = px.line(peak_ccu_df, x='year', y='total_peak_ccu', title='Total Peak CCU Over the Years')
    st.plotly_chart(fig_peak_ccu)

   # drill down to months
    st.sidebar.subheader("Filter By Year")
    year_options = release_date_query["year"]
    selected_year = st.sidebar.selectbox("Pick Year", year_options)

    if selected_year:
        st.subheader(f"📊 Data for Year {selected_year} (by Month)")
        
        
        specific_year_query = f"""
        SELECT YEAR(d.release_date) AS year, MONTH(d.release_date) AS month, 
            COUNT(fg.game_id) AS total_games, 
            AVG(fg.price) AS avg_price, 
            SUM(fg.peak_ccu) AS total_peak_ccu
        FROM fact_game fg
        JOIN dimm_date d ON fg.date_id = d.date_id
        WHERE YEAR(d.release_date) = {selected_year}
        GROUP BY YEAR(d.release_date), MONTH(d.release_date)
        ORDER BY MONTH(d.release_date);
        """
        year_df = pd.read_sql(specific_year_query, engine)

        #graphs for drill down
        fig_year_total_games = px.line(year_df, x='month', y='total_games', 
                                    title=f"Total Number of Games Released in {selected_year} (by Month)")
        st.plotly_chart(fig_year_total_games)

        fig_year_avg_price = px.line(year_df, x='month', y='avg_price', 
                                    title=f"Average Game Price in {selected_year} (by Month)")
        st.plotly_chart(fig_year_avg_price)

        fig_year_peak_ccu = px.line(year_df, x='month', y='total_peak_ccu', 
                                    title=f"Total Peak CCU in {selected_year} (by Month)")
        st.plotly_chart(fig_year_peak_ccu)

elif data_view == "Developer Data":
    st.header("🎮 Developer Data")

    #Developer Section
    developer_options = developer_options_query['name']
    selected_developer = st.sidebar.selectbox("Pick Developer", developer_options)

    if selected_developer:
        st.subheader(f"📊 Data for Developer: {selected_developer}")
        
        # Developer reviews
        developer_reviews_query = f"""
        SELECT fg.name AS game_name, fg.positive_reviews, fg.negative_reviews
        FROM fact_game fg
        JOIN game_developer gd ON fg.game_id = gd.game_id
        JOIN dimm_developer dd ON gd.developer_id = dd.developer_id
        WHERE dd.name = '{selected_developer}';
        """
        reviews_df = pd.read_sql(developer_reviews_query, engine)
        fig_reviews = px.bar(reviews_df, x='game_name', y=['positive_reviews', 'negative_reviews'], title=f'Positive and Negative Reviews for Games by {selected_developer}', barmode='group',     color_discrete_map={
        'positive_reviews': 'blue',  # Set positive reviews to blue
        'negative_reviews': 'orange'    # Set negative reviews to red
    })
        st.plotly_chart(fig_reviews)


elif data_view == "Genre Data":
    st.header("🎮 Genre Data")

    #Genre Section
    genre_options = genre_options_query['name']
    selected_genre = st.sidebar.selectbox("Pick Genre", genre_options)

    if selected_genre:
        st.subheader(f"📊 Data for Genre: {selected_genre}")

        # Total games developed for genre over the years
        genre_games_query = f"""
        SELECT YEAR(d.release_date) AS release_year, COUNT(fg.game_id) AS total_games
        FROM fact_game fg
        JOIN game_genre gg ON fg.game_id = gg.game_id
        JOIN dimm_genre dg ON gg.genre_id = dg.genre_id
        JOIN dimm_date d ON fg.date_id = d.date_id
        WHERE dg.name = '{selected_genre}'
        GROUP BY YEAR(d.release_date)
        ORDER BY YEAR(d.release_date);
        """
        genre_games_df = pd.read_sql(genre_games_query, engine)
        fig_genre_games = px.line(genre_games_df, x='release_year', y='total_games', title=f"Total Games Developed for {selected_genre} Over the Years")
        st.plotly_chart(fig_genre_games)

        # Total peak CCU for the genre over the years
        genre_ccu_query = f"""
        SELECT YEAR(d.release_date) AS release_year, SUM(fg.peak_ccu) AS total_peak_ccu
        FROM fact_game fg
        JOIN game_genre gg ON fg.game_id = gg.game_id
        JOIN dimm_genre dg ON gg.genre_id = dg.genre_id
        JOIN dimm_date d ON fg.date_id = d.date_id
        WHERE dg.name = '{selected_genre}'
        GROUP BY YEAR(d.release_date)
        ORDER BY YEAR(d.release_date);
        """
        genre_ccu_df = pd.read_sql(genre_ccu_query, engine)
        fig_genre_ccu = px.line(genre_ccu_df, x='release_year', y='total_peak_ccu', title=f"Total Peak CCU for {selected_genre} Over the Years")
        st.plotly_chart(fig_genre_ccu)

elif data_view == "Tag Data":
    st.header("🏷️ Tag Data")

    st.sidebar.subheader("Select Tags")
    available_tags = tag_options_query['name']
    selected_tags = st.sidebar.multiselect("Pick up to 5 Tags", available_tags, max_selections=5)

    if selected_tags:
        st.subheader(f"Number of Games Over the Years for Selected Tags")

        #number of games per year for each selected tag
        tag_filter = "', '".join(selected_tags)
        year_tag_query = f"""
        SELECT t.name AS tag_name, YEAR(d.release_date) AS release_year, COUNT(gt.game_id) AS game_count
        FROM game_tag gt
        JOIN dimm_tag t ON gt.tag_id = t.tag_id
        JOIN fact_game fg ON gt.game_id = fg.game_id
        JOIN dimm_date d ON fg.date_id = d.date_id
        WHERE t.name IN ('{tag_filter}')
        GROUP BY t.name, YEAR(d.release_date)
        ORDER BY release_year;
        """
        year_tag_df = pd.read_sql(year_tag_query, engine)

        if not year_tag_df.empty:
            fig_tag_line = px.line(year_tag_df, x='release_year', y='game_count', color='tag_name',
                                title='Number of Games Over the Years for Selected Tags',
                                labels={'release_year': 'Year', 'game_count': 'Number of Games', 'tag_name': 'Tag'})
            st.plotly_chart(fig_tag_line)
        else:
            st.write(f"No data available for the selected tags: {', '.join(selected_tags)}")

