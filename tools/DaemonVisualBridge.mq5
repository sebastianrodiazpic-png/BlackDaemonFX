//+------------------------------------------------------------------+
//|                                           DaemonVisualBridge.mq5 |
//|                                  Copyright 2026, BlackDaemonFX   |
//|                 Visualizador de Order Blocks, FVGs y Liquidez    |
//+------------------------------------------------------------------+
#property copyright   "DaemonBlackFx"
#property link        "https://github.com/sebastianrodiazpic-png/BlackDaemonFX"
#property version     "2.00"
#property description "Dibuja en tiempo real sobre el gráfico de MT5 los Order Blocks, FVGs y Barridos generados por Python"
#property indicator_chart_window
#property indicator_plots 0

input int      InpRefreshSeconds = 1;        // Frecuencia de refresco (segundos)
input color    InpColorH1_OB     = C'30,144,255'; // Color Order Block H1 (Azul translúcido)
input color    InpColorBull_FVG  = C'46,139,87';  // Color FVG Alcista M15 (Verde suave)
input color    InpColorBear_FVG  = C'205,92,92';  // Color FVG Bajista M15 (Rojo suave)
input color    InpColorSweep     = C'255,215,0';  // Color Barrido de Liquidez (Dorado)

#define PREFIX "BD_VISUAL_"

//+------------------------------------------------------------------+
//| Inicialización del indicador                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   EventSetTimer(InpRefreshSeconds);
   RefreshVisualZones();
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Desinicialización: Limpieza de objetos gráficos en el gráfico    |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   CleanObjects();
   ChartRedraw(0);
}

//+------------------------------------------------------------------+
//| Evento Timer periódico                                           |
//+------------------------------------------------------------------+
void OnTimer()
{
   RefreshVisualZones();
}

//+------------------------------------------------------------------+
//| Cálculo del indicador                                            |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
   return(rates_total);
}

//+------------------------------------------------------------------+
//| Elimina objetos con el prefijo del bot                           |
//+------------------------------------------------------------------+
void CleanObjects()
{
   for(int i = ObjectsTotal(0, 0, -1) - 1; i >= 0; i--)
   {
      string name = ObjectName(0, i, 0, -1);
      if(StringFind(name, PREFIX) == 0)
      {
         ObjectDelete(0, name);
      }
   }
}

//+------------------------------------------------------------------+
//| Lee el archivo JSON emitido por Python y dibuja las zonas        |
//+------------------------------------------------------------------+
void RefreshVisualZones()
{
   string sym = _Symbol;
   StringReplace(sym, " ", "_");
   string filename = "blackdaemon_visual_bridge_" + sym + ".json";

   int handle = FileOpen(filename, FILE_READ | FILE_TXT | FILE_ANSI | FILE_COMMON);
   if(handle == INVALID_HANDLE)
   {
      // Fallback a la carpeta local del terminal
      handle = FileOpen(filename, FILE_READ | FILE_TXT | FILE_ANSI);
   }

   if(handle == INVALID_HANDLE)
      return;

   string content = "";
   while(!FileIsEnding(handle))
   {
      content += FileReadString(handle);
   }
   FileClose(handle);

   if(StringLen(content) < 10)
      return;

   // Limpiar zonas previas antes de redibujar actualizadas
   CleanObjects();

   // Parseo ligero de bloques JSON
   int searchPos = 0;
   while(true)
   {
      int zoneStart = StringFind(content, "{\"zone_id\"", searchPos);
      if(zoneStart < 0)
      {
         zoneStart = StringFind(content, "{\"zone_id\":", searchPos);
         if(zoneStart < 0) break;
      }

      int zoneEnd = StringFind(content, "}", zoneStart);
      if(zoneEnd < 0) break;

      string block = StringSubstr(content, zoneStart, zoneEnd - zoneStart + 1);
      RenderZoneFromBlock(block);

      searchPos = zoneEnd + 1;
   }

   ChartRedraw(0);
}

//+------------------------------------------------------------------+
//| Renderiza una zona individual a partir de un fragmento JSON      |
//+------------------------------------------------------------------+
void RenderZoneFromBlock(string block)
{
   string zone_id   = ExtractJsonValue(block, "zone_id");
   string zone_type = ExtractJsonValue(block, "zone_type");
   string timeframe = ExtractJsonValue(block, "timeframe");
   string direction = ExtractJsonValue(block, "direction");
   double price_high = StringToDouble(ExtractJsonValue(block, "price_high"));
   double price_low  = StringToDouble(ExtractJsonValue(block, "price_low"));
   string time_start = ExtractJsonValue(block, "time_start");
   string time_end   = ExtractJsonValue(block, "time_end");
   string label      = ExtractJsonValue(block, "label");

   datetime t1 = ParseIsoTime(time_start);
   datetime t2 = ParseIsoTime(time_end);
   if(t2 <= t1) t2 = t1 + 3600 * 4;

   string objName = PREFIX + zone_id;

   if(zone_type == "ORDER_BLOCK")
   {
      // Rectángulo de Order Block H1
      ObjectCreate(0, objName, OBJ_RECTANGLE, 0, t1, price_high, t2, price_low);
      ObjectSetInteger(0, objName, OBJPROP_COLOR, InpColorH1_OB);
      ObjectSetInteger(0, objName, OBJPROP_BGCOLOR, InpColorH1_OB);
      ObjectSetInteger(0, objName, OBJPROP_FILL, true);
      ObjectSetInteger(0, objName, OBJPROP_BACK, true);
      ObjectSetString(0, objName, OBJPROP_TOOLTIP, label);
   }
   else if(zone_type == "FVG")
   {
      // Rectángulo de FVG M15
      color fvgColor = (direction == "BULLISH" || direction == "BUY") ? InpColorBull_FVG : InpColorBear_FVG;
      ObjectCreate(0, objName, OBJ_RECTANGLE, 0, t1, price_high, t2, price_low);
      ObjectSetInteger(0, objName, OBJPROP_COLOR, fvgColor);
      ObjectSetInteger(0, objName, OBJPROP_BGCOLOR, fvgColor);
      ObjectSetInteger(0, objName, OBJPROP_FILL, true);
      ObjectSetInteger(0, objName, OBJPROP_BACK, true);
      ObjectSetString(0, objName, OBJPROP_TOOLTIP, label);
   }
   else if(zone_type == "SWEEP")
   {
      // Línea punteada de Barrido de Liquidez
      ObjectCreate(0, objName, OBJ_TREND, 0, t1, price_high, t2, price_high);
      ObjectSetInteger(0, objName, OBJPROP_COLOR, InpColorSweep);
      ObjectSetInteger(0, objName, OBJPROP_STYLE, STYLE_DOT);
      ObjectSetInteger(0, objName, OBJPROP_WIDTH, 2);
      ObjectSetInteger(0, objName, OBJPROP_RAY_RIGHT, true);
      ObjectSetString(0, objName, OBJPROP_TOOLTIP, label);
   }

   // Etiqueta de texto auxiliar sobre la zona
   string textName = objName + "_TXT";
   ObjectCreate(0, textName, OBJ_TEXT, 0, t1, price_high);
   ObjectSetString(0, textName, OBJPROP_TEXT, label);
   ObjectSetInteger(0, textName, OBJPROP_COLOR, clrWhite);
   ObjectSetInteger(0, textName, OBJPROP_FONTSIZE, 8);
}

//+------------------------------------------------------------------+
//| Parser básico de valores en un bloque JSON                       |
//+------------------------------------------------------------------+
string ExtractJsonValue(string json, string key)
{
   string needle = "\"" + key + "\":";
   int pos = StringFind(json, needle);
   if(pos < 0)
   {
      needle = "\"" + key + "\" :";
      pos = StringFind(json, needle);
      if(pos < 0) return "";
   }

   pos += StringLen(needle);
   while(pos < StringLen(json) && (StringGetCharacter(json, pos) == ' ' || StringGetCharacter(json, pos) == '\"'))
      pos++;

   int endPos = pos;
   while(endPos < StringLen(json))
   {
      ushort c = StringGetCharacter(json, endPos);
      if(c == '\"' || c == ',' || c == '}')
         break;
      endPos++;
   }

   return StringSubstr(json, pos, endPos - pos);
}

//+------------------------------------------------------------------+
//| Convierte timestamp ISO a datetime nativo de MQL5                |
//+------------------------------------------------------------------+
datetime ParseIsoTime(string iso)
{
   if(StringLen(iso) < 10) return TimeCurrent();
   // Formato esperado: YYYY-MM-DDTHH:MM:SS
   string datePart = StringSubstr(iso, 0, 10);
   StringReplace(datePart, "-", ".");
   string timePart = "00:00:00";
   if(StringLen(iso) >= 19)
      timePart = StringSubstr(iso, 11, 8);

   return StringToTime(datePart + " " + timePart);
}
//+------------------------------------------------------------------+
