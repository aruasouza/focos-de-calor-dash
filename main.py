from dash import Dash, html, dcc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime
import io
from base64 import b64encode
from dash.dependencies import Output, Input, State
from dash import callback_context
import urllib

app = Dash(__name__)

font_color = 'rgb(100,100,100)'
map_style = "stamen-terrain"

def get_data():
    url = 'http://queimadas.dgi.inpe.br/api/focos'
    print('Obtendo dados...')
    try:
        req = requests.get(url)
        df = pd.json_normalize(req.json())
        df = df.rename(columns={'properties.longitude':'Longitude','properties.latitude':'Latitude','properties.pais':'País',
        'properties.estado':'Estado','properties.municipio':'Município','properties.risco_fogo':'Risco de Fogo',
        'properties.precipitacao':'Precipitação','properties.numero_dias_sem_chuva':'Dias sem Chuva','properties.data_hora_gmt':'Data',
        'geometry.type':'geometry_type','geometry.coordinates':'geometry_coordinates','properties.satelite':'Satélite'})
        df.to_csv('dados_backup.csv',index = False,sep = ';',decimal = ',')
        time_df = pd.DataFrame({'time':[datetime.now()]})
        time_df.to_csv('time.csv',index = False)
        # backup = False
        print('Success')
    except Exception:
        print('O request falhou')
        df = pd.read_csv('dados_backup.csv',sep = ';',decimal = ',')
        # backup = True
        # time = pd.read_csv('time.csv').loc[0,'time']
    return df

def inicial_figure():
    fig = px.density_mapbox(pd.DataFrame({'Município':[],'Latitude':[],'Longitude':[],'País':[],'Estado':[]}),
                            lat="Latitude", lon="Longitude",radius = 4, hover_name="Município",
                            hover_data=["País",'Estado'], zoom=3,color_continuous_scale = 'Hot')
    fig.update_layout(mapbox_style=map_style,transition_duration=500,margin=dict(l=0,r=0,b=0,t=0))
    return fig

@app.callback(Output('mapa','figure'),Input('data','data'))
def update_figure(data):
    df = pd.read_json(data, orient='split')
    fig = px.density_mapbox(df, lat="Latitude", lon="Longitude",radius = 4, hover_name="Município",
        hover_data=["País",'Estado'], zoom=3,color_continuous_scale = 'Hot')

    fig.update_layout(mapbox_style=map_style,transition_duration=500,margin=dict(l=0,r=0,b=0,t=0))
    fig.update(layout_coloraxis_showscale=False)
    return fig

@app.callback(Output('data', 'data'), Input('dummy', 'children'), State('data', 'data'))
def update_data(dummy, data):
    if not data or not callback_context.triggered:
        data = get_data()
    return data.to_json(orient='split')

@app.callback(Output('baixar_mapa','href'),Input('mapa','figure'))
def create_html(figure):
    fig = go.Figure(figure)
    buffer = io.StringIO()
    fig.write_html(buffer)
    html_bytes = buffer.getvalue().encode()
    encoded = b64encode(html_bytes).decode()
    return "data:text/html;base64," + encoded

@app.callback(Output('baixar_dados','href'),Input('data','data'))
def create_csv(data):
    df = pd.read_json(data, orient='split')
    csv = df.to_csv(index = False)
    return "data:text/csv;charset=utf-8," + urllib.parse.quote(csv)

@app.callback(Output('info','style'),Output('fade','style'),Output('sobre','disabled'),Input('sobre','n_clicks'),Input('closeInfo','n_clicks'))
def show_info(open,close):
    if open > close:
        return {'display':'block'},{'display':'block'},True
    return {'display': 'none'},{'display': 'none'},False

app.layout = html.Div([
    html.Div(id='dummy', style={'display': 'none'}),
    dcc.Store(id = 'data'),
    html.H1('Focos de Calor na América do Sul',
            style = {'font-family':'helvetica','background-color':'white','border-radius':'5px',
                        'padding':'10px','color':font_color,'margin':'10px','float':'left','font-size':'23px'},id = 'title'),
    html.Div([
        html.A(html.Button('Sobre',id = 'sobre',className = 'menuButton',n_clicks = 0)),
        html.A(html.Button('Baixar Dados',className = 'menuButton'),id = 'baixar_dados',download = 'focos_de_calor.csv'),
        html.A(html.Button('Baixar Mapa',className = 'menuButton'),id = 'baixar_mapa',download = 'focos_de_calor.html')],
        style = {'position': 'fixed', 'top': '75', 'left': '5'}),
    dcc.Graph(
        id='mapa',
        figure = inicial_figure(),
        style = {'position': 'fixed', 'top': '0', 'left': '0','height': '100vh', 'width': '100vw', 'z-index': '-1'}
    ),
    html.Div(id = 'fade'),
    html.Div([
        html.Button('X',id = 'closeInfo',n_clicks = 0),
        html.Div([
            html.H2('Sobre o projeto:'),
            html.P('Dados das últimas 24h.'),
            html.P(['Fonte dos dados: ',html.A('BDQueimadas',href = 'https://queimadas.dgi.inpe.br/queimadas/portal')]),
            html.P(['Criado por: ',html.A('Aruã Viggiano Souza',href = 'https://www.linkedin.com/in/aru%C3%A3-viggiano-souza/')])
        ],id = 'blocoTexto')],id = 'info')
])

if __name__ == '__main__':
    app.run_server(debug=True,port = 80)#,host = '0.0.0.0')