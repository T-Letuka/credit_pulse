from sqlalchemy import create_engine
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import os
from dotenv import load_dotenv


# --- LOAD DATA FROM CSVs ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

df_impaired   = pd.read_csv(os.path.join(DATA_DIR, 'df_impaired.csv'))
df_rate       = pd.read_csv(os.path.join(DATA_DIR, 'df_rate.csv'))
df_enquiries  = pd.read_csv(os.path.join(DATA_DIR, 'df_enquiries.csv'))
df_tug        = pd.read_csv(os.path.join(DATA_DIR, 'df_tug.csv'))
df_disputes   = pd.read_csv(os.path.join(DATA_DIR, 'df_disputes.csv'))
df_episodes   = pd.read_csv(os.path.join(DATA_DIR, 'df_recovery.csv'))

# --- SORT ALL DATAFRAMES ---
for df_loop in [df_impaired, df_rate, df_enquiries, df_tug, df_disputes]:
    df_loop['sort_key'] = df_loop['year'] * 100 + df_loop['month']
    df_loop.sort_values('sort_key', inplace=True)
    df_loop.reset_index(drop=True, inplace=True)

# --- KPI VALUES ---
latest_impaired  = df_impaired['value_millions'].iloc[-1]
latest_rate      = df_rate['impairment_rate_pct'].iloc[-1]
first_impaired   = df_impaired['value_millions'].iloc[0]
change_pct       = round((latest_impaired - first_impaired) / first_impaired * 100, 1)
latest_disputes  = df_disputes['disputes_lodged'].iloc[-1]
latest_resolution = df_disputes['resolution_rate_pct'].iloc[-1]

# --- THEME ---
DARK_BG = '#000000'
CARD_BG = '#001524'
ACCENT_RED = '#d00000'
ACCENT_GREEN = '#8ac926'
ACCENT_BLUE = '#3b82f6'
ACCENT_AMBER = '#f59e0b'
ACCENT_PURPLE = '#8b5cf6'
TEXT_COLOR = '#f1faee'
GRID_COLOR = '#1e2a3a'

chart_layout = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color=TEXT_COLOR, family='DM Sans, sans-serif'),
    yaxis=dict(gridcolor=GRID_COLOR, showgrid=True),
    margin=dict(l=40, r=20, t=40, b=60),
    legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(size=11)),
    hovermode='x unified'
)

def category_xaxis(labels):
    year_labels = []
    seen_years = set()
    for lbl in labels:
        year = lbl[-2:]
        if year not in seen_years:
            seen_years.add(year)
            year_labels.append(lbl)
    return dict(
        type='category',
        categoryorder='array',
        categoryarray=labels,
        tickmode='array',
        tickvals=year_labels,
        ticktext=year_labels,
        gridcolor=GRID_COLOR,
        showgrid=True,
        tickangle=-45,
        tickfont=dict(size=9)
    )


ordered_labels = df_impaired['period_label'].tolist()
covid_label = df_impaired[df_impaired['period_label'].str.strip() == "Mar'20"]['period_label'].iloc[0]

# FIG 1
fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=df_impaired['period_label'], y=df_impaired['value_millions'],
    mode='lines', name='Impaired Consumers',
    line=dict(color=ACCENT_RED, width=2.5),
    fill='tozeroy', fillcolor='rgba(239,68,68,0.1)'
))
fig1.update_layout(
    title=dict(text='Impaired Consumers Over Time', font=dict(size=14)),
    xaxis=category_xaxis(ordered_labels),
    **chart_layout
)
fig1.add_shape(type='line', xref='x', yref='paper',
    x0=covid_label, x1=covid_label, y0=0, y1=1,
    line=dict(color='white', dash='dash'))
fig1.add_annotation(xref='x', yref='paper',
    x=covid_label, y=1.0, text='COVID-19',
    showarrow=False, font=dict(color='white'), xanchor='left')

# FIG 2
fig2 = go.Figure()
fig2.add_trace(go.Scatter(
    x=df_rate['period_label'], y=df_rate['impairment_rate_pct'],
    mode='lines', name='Impairment Rate %',
    line=dict(color=ACCENT_AMBER, width=2.5),
    fill='tozeroy', fillcolor='rgba(245,158,11,0.1)'
))
fig2.update_layout(
    title=dict(text='Impairment Rate (% of Credit-Active Consumers)', font=dict(size=14)),
    xaxis=category_xaxis(df_rate['period_label'].tolist()),
    **chart_layout
)

# FIG 3
fig3 = go.Figure()
colors = [ACCENT_BLUE, ACCENT_GREEN, ACCENT_RED, ACCENT_AMBER, ACCENT_PURPLE]
enq_labels = df_enquiries.drop_duplicates('sort_key').sort_values('sort_key')['period_label'].tolist()
for i, sector in enumerate(df_enquiries['sector'].unique()):
    df_s = df_enquiries[df_enquiries['sector'] == sector].sort_values('sort_key').reset_index(drop=True)
    fig3.add_trace(go.Scatter(
        x=df_s['period_label'], y=df_s['enquiries_millions'],
        mode='lines', name=sector,
        line=dict(color=colors[i % len(colors)], width=2)
    ))
fig3.update_layout(
    title=dict(text='Credit Enquiries by Sector', font=dict(size=14)),
    xaxis=category_xaxis(enq_labels),
    **chart_layout
)

# FIG 4
fig4 = go.Figure()
fig4.add_trace(go.Scatter(
    x=df_tug['period_label'], y=df_tug['good_standing'],
    mode='lines', name='Good Standing',
    line=dict(color=ACCENT_GREEN, width=2.5)
))
fig4.add_trace(go.Scatter(
    x=df_tug['period_label'], y=df_tug['impaired'],
    mode='lines', name='Impaired',
    line=dict(color=ACCENT_RED, width=2.5)
))
fig4.update_layout(
    title=dict(text='Good Standing vs Impaired Consumers', font=dict(size=14)),
    xaxis=category_xaxis(df_tug['period_label'].tolist()),
    **chart_layout
)

# FIG 5
fig5 = go.Figure()
fig5.add_trace(go.Bar(
    x=df_disputes['period_label'], y=df_disputes['disputes_lodged'],
    name='Disputes Lodged', marker_color=ACCENT_BLUE, opacity=0.8
))
fig5.add_trace(go.Scatter(
    x=df_disputes['period_label'], y=df_disputes['resolution_rate_pct'],
    name='Resolution Rate %', yaxis='y2',
    line=dict(color=ACCENT_AMBER, width=2.5)
))
fig5.update_layout(
    title=dict(text='Disputes Lodged & Resolution Rate', font=dict(size=14)),
    xaxis=category_xaxis(df_disputes['period_label'].tolist()),
    yaxis2=dict(title='Resolution Rate (%)', overlaying='y', side='right',
                gridcolor=GRID_COLOR, tickfont=dict(color=ACCENT_AMBER)),
    **chart_layout
)

# FIG 6
df_rec = df_impaired.copy()
fig6 = go.Figure()
fig6.add_trace(go.Scatter(
    x=df_rec['period_label'], y=df_rec['value_millions'],
    mode='lines', name='Impaired Consumers',
    line=dict(color=ACCENT_RED, width=2),
    fill='tozeroy', fillcolor='rgba(239,68,68,0.05)'
))
for _, ep in df_episodes.iterrows():
    fig6.add_vrect(
        x0=ep['start_period'], x1=ep['end_period'],
        fillcolor='rgba(16,185,129,0.12)',
        layer='below', line_width=0
    )
for _, ep in df_episodes[df_episodes['sustained']].iterrows():
    fig6.add_annotation(
        x=ep['start_period'],
        y=df_rec[df_rec['period_label'] == ep['start_period']]['value_millions'].iloc[0] - 0.3,
        text=f"{ep['duration_quarters']}Q",
        showarrow=False,
        font=dict(color=ACCENT_GREEN, size=10),
        bgcolor='rgba(16,185,129,0.15)',
        bordercolor=ACCENT_GREEN, borderwidth=1
    )
fig6.update_layout(
    title=dict(text='The Invisible Recovery — Every Green Zone Was Temporary', font=dict(size=14)),
    xaxis=category_xaxis(df_rec['period_label'].tolist()),
    **chart_layout
)

# --- DASH APP ---
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

CARD = {'background': CARD_BG, 'border': f'1.5px solid {GRID_COLOR}',
        'borderRadius': '12px', 'padding': '24px'}
MUTED = {'color': '#64748b', 'fontSize': '12px', 'marginBottom': '12px'}

app.layout = html.Div(style={'backgroundColor': DARK_BG, 'minHeight': '100vh',
                              'fontFamily': 'DM Sans, sans-serif'}, children=[

    # HEADER
    html.Div(style={'padding': '48px 48px 32px', 'borderBottom': f'1px solid {GRID_COLOR}'}, children=[
        html.P("NCR CREDIT BUREAU MONITOR · 2007–2024",
               style={'color': ACCENT_RED, 'fontSize': '14px', 'letterSpacing': '3px', 'marginBottom': '12px'}),
        html.H1("The State of Consumer Credit in South Africa",
                style={'color': '#fff', 'fontSize': '50px', 'fontWeight': '400', 'marginBottom': '12px'}),
        html.P("17 years of National Credit Regulator data revealing how South African consumers have navigated credit access, debt stress, and financial distress.",
               style={'color': '#64748b', 'fontSize': '15px', 'maxWidth': '600px'}),
    ]),

    # KPI STRIP
    dbc.Row(style={'margin': '0', 'borderBottom': f'1px solid {GRID_COLOR}'}, children=[
        dbc.Col(html.Div([
            html.P("IMPAIRED CONSUMERS", style={'color': '#64748b', 'fontSize': '11px', 'letterSpacing': '2px'}),
            html.H2(f"{latest_impaired:.1f}M", style={'color': '#fff', 'fontSize': '36px'}),
            html.P(f"+{change_pct}% since 2007", style={'color': ACCENT_RED, 'fontSize': '12px'}),
        ], style={'padding': '28px 32px', 'borderRight': f'1px solid {GRID_COLOR}'})),
        dbc.Col(html.Div([
            html.P("IMPAIRMENT RATE", style={'color': '#64748b', 'fontSize': '11px', 'letterSpacing': '2px'}),
            html.H2(f"{latest_rate:.1f}%", style={'color': '#fff', 'fontSize': '36px'}),
            html.P("Of all credit-active consumers", style={'color': '#64748b', 'fontSize': '12px'}),
        ], style={'padding': '28px 32px', 'borderRight': f'1px solid {GRID_COLOR}'})),
        dbc.Col(html.Div([
            html.P("DISPUTES LODGED", style={'color': '#64748b', 'fontSize': '11px', 'letterSpacing': '2px'}),
            html.H2(f"{int(latest_disputes):,}", style={'color': '#fff', 'fontSize': '36px'}),
            html.P("Latest quarter on record", style={'color': '#64748b', 'fontSize': '12px'}),
        ], style={'padding': '28px 32px', 'borderRight': f'1px solid {GRID_COLOR}'})),
        dbc.Col(html.Div([
            html.P("RESOLUTION RATE", style={'color': '#64748b', 'fontSize': '11px', 'letterSpacing': '2px'}),
            html.H2(f"{latest_resolution:.1f}%", style={'color': '#fff', 'fontSize': '36px'}),
            html.P("Resolved in consumer's favour", style={'color': '#64748b', 'fontSize': '12px'}),
        ], style={'padding': '28px 32px'})),
    ]),

# SO WHAT SECTION 
html.Div(style={'padding': '32px 48px', 'borderBottom': f'1px solid {GRID_COLOR}'}, children=[

    html.P("SO WHAT - IMPLICATIONS FOR STAKEHOLDERS",
           style={'color': '#64748b', 'fontSize': '11px', 'letterSpacing': '3px',
                  'marginBottom': '24px'}),

    dbc.Row([
        # FOR LENDERS
        dbc.Col(html.Div(style={
            'borderLeft': f'2px solid {ACCENT_RED}',
            'paddingLeft': '20px',
            'paddingTop': '4px',
            'paddingBottom': '4px',
        }, children=[
            html.P("FOR LENDERS", style={
                'color': ACCENT_RED, 'fontSize': '11px',
                'letterSpacing': '2px', 'fontWeight': '600',
                'marginBottom': '8px'
            }),
            html.P("The constant impairment rate raises the possibility that structural default risk in the South African market may be systematically underestimated by conventional credit scoring models, which are predicated on the idea that consumers recover in between credit events.",
                   style={'color': TEXT_COLOR, 'fontSize': '13px', 'lineHeight': '1.7',
                          'margin': '0'}),
        ]), width=4),

        # FOR THE NCR
        dbc.Col(html.Div(style={
            'borderLeft': f'2px solid {ACCENT_AMBER}',
            'paddingLeft': '20px',
            'paddingTop': '4px',
            'paddingBottom': '4px',
        }, children=[
            html.P("FOR THE NCR", style={
                'color': ACCENT_AMBER, 'fontSize': '11px',
                'letterSpacing': '2px', 'fontWeight': '600',
                'marginBottom': '8px'
            }),
            html.P("Recovery episodes average 2.1 quarters before reversing. No intervention has produced a sustained decline. The question worth investigating is why.",
                   style={'color': TEXT_COLOR, 'fontSize': '13px', 'lineHeight': '1.7',
                          'margin': '0'}),
        ]), width=4),

        # FOR POLICY
        dbc.Col(html.Div(style={
            'borderLeft': f'2px solid {ACCENT_BLUE}',
            'paddingLeft': '20px',
            'paddingTop': '4px',
            'paddingBottom': '4px',
        }, children=[
            html.P("FOR POLICY", style={
                'color': ACCENT_BLUE, 'fontSize': '11px',
                'letterSpacing': '2px', 'fontWeight': '600',
                'marginBottom': '8px'
            }),
            html.P("The post-COVID squeeze starting 2022 is more damaging than COVID itself. Payment holidays delayed, not prevented the damage.",
                   style={'color': TEXT_COLOR, 'fontSize': '13px', 'lineHeight': '1.7',
                          'margin': '0'}),
        ]), width=4),
        #for consumers 

         dbc.Col(html.Div(style={
            'borderLeft': f'2px solid {ACCENT_GREEN}',
            'paddingLeft': '20px',
            'paddingTop': '4px',
            'paddingBottom': '4px',
        }, children=[
            html.P("FOR CONSUMERS", style={
                'color': ACCENT_GREEN, 'fontSize': '11px',
                'letterSpacing': '2px', 'fontWeight': '600',
                'marginBottom': '8px'
            }),
            html.P("the rising dispute volume suggests growing awareness of credit rights. However, the resolution rate and persistent impairment levels indicate that awareness alone is insufficient without structural intervention in how credit is extended and recovered in South Africa.",
                   style={'color': TEXT_COLOR, 'fontSize': '13px', 'lineHeight': '1.7',
                          'margin': '0'}),
        ]), width=4),

    ], style={'gap': '8px'}),
]),

    # MAIN
    html.Div(style={'padding': '32px 48px'}, children=[

        # CHART 1
        html.Div(style={**CARD, 'marginBottom': '20px'}, children=[
            html.P("Total number of credit-active consumers with impaired records, tracked quarterly from June 2007 to September 2024.", style=MUTED),
            dcc.Graph(figure=fig1, config={'displayModeBar': False}, style={'height': '360px'})
        ]),

        # CHARTS 2 & 4
        dbc.Row(style={'marginBottom': '20px'}, children=[
            dbc.Col(html.Div(style=CARD, children=[
                html.P("Impaired consumers as a percentage of all credit-active consumers.", style=MUTED),
                dcc.Graph(figure=fig2, config={'displayModeBar': False}, style={'height': '300px'})
            ]), width=6),
            dbc.Col(html.Div(style=CARD, children=[
                html.P("Consumers in good standing vs impaired consumers over time.", style=MUTED),
                dcc.Graph(figure=fig4, config={'displayModeBar': False}, style={'height': '300px'})
            ]), width=6),
        ]),

        # CHARTS 3 & 5
        dbc.Row(style={'marginBottom': '20px'}, children=[
            dbc.Col(html.Div(style=CARD, children=[
                html.P("Credit enquiries by sector — banks, retailers, telecoms and others.", style=MUTED),
                dcc.Graph(figure=fig3, config={'displayModeBar': False}, style={'height': '300px'})
            ]), width=6),
            dbc.Col(html.Div(style=CARD, children=[
                html.P("Disputes lodged and resolution rate in favour of consumers.", style=MUTED),
                dcc.Graph(figure=fig5, config={'displayModeBar': False}, style={'height': '300px'})
            ]), width=6),
        ]),

        # CHART 6
        html.Div(style=CARD, children=[
            html.P("Every recovery episode identified across 17 years. Green zones mark declining impairment periods.", style=MUTED),
            dcc.Graph(figure=fig6, config={'displayModeBar': False}, style={'height': '380px'})
        ]),
    ]),

    # FOOTER
    html.Div(style={'padding': '24px 48px', 'borderTop': f'1px solid {GRID_COLOR}',
                    'display': 'flex', 'justifyContent': 'space-between'}, children=[
        html.P("CreditPulse SA · Act 1 - Descriptive Analysis · Data: National Credit Regulator",
               style={'color': '#64748b', 'fontSize': '12px'}),
        html.Div([
            html.Span("Python", style={'border': f'1px solid {GRID_COLOR}', 'padding': '4px 10px',
                                        'borderRadius': '4px', 'color': '#64748b', 'fontSize': '11px', 'marginRight': '8px'}),
            html.Span("MySQL", style={'border': f'1px solid {GRID_COLOR}', 'padding': '4px 10px',
                                       'borderRadius': '4px', 'color': '#64748b', 'fontSize': '11px', 'marginRight': '8px'}),
            html.Span("Plotly Dash", style={'border': f'1px solid {GRID_COLOR}', 'padding': '4px 10px',
                                             'borderRadius': '4px', 'color': '#64748b', 'fontSize': '11px'}),
        ])
    ]),
])

server = app.server
if __name__ == '__main__':
    app.run(debug=True, port=8050)