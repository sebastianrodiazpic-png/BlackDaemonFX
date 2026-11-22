//+------------------------------------------------------------------+
//|                                              ICT_Strategy_EA.mq5 |
//|                                  Copyright 2026, BlackDaemonFX   |
//|                    Estrategia Institucional ICT (AMD + FVG + CE) |
//+------------------------------------------------------------------+
#property copyright   "Copyright 2026, BlackDaemonFX"
#property link        "https://github.com/sebastianrodiazpic-png/BlackDaemonFX"
#property version     "2.00"
#property description "Asesor Experto ICT Profesional basado en Smart Money Concepts:"
#property description "1. Acumulacion: Rango Asiatico (Asian Range)."
#property description "2. Manipulacion: Barrido de Liquidez / Judas Swing."
#property description "3. Distribucion: Market Structure Shift (MSS) + Fair Value Gap (FVG)."
#property description "4. Entrada: Mitigacion en Consequent Encroachment (50% CE) o Borde de FVG."
#property description "5. Gestion de Riesgo Dinamico, Break Even y Trailing Stop."

//+------------------------------------------------------------------+
//| Inclusiones de la Libreria Estandar MQL5 (POO)                    |
//+------------------------------------------------------------------+
#include <Trade\Trade.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>

//+------------------------------------------------------------------+
//| Enumeraciones del Sistema                                        |
//+------------------------------------------------------------------+
enum ENUM_RISK_MODE
{
   RISK_PERCENT,    // Porcentaje de Riesgo sobre Balance
   RISK_FIXED_LOT   // Lote Fijo Manual
};

enum ENUM_ENTRY_MODE
{
   ENTRY_FVG_EDGE,  // Entrada al Borde del FVG
   ENTRY_FVG_CE_50  // Entrada al Consequent Encroachment (50% CE)
};

//+------------------------------------------------------------------+
//| Parametros de Entrada (Inputs Agrupados con Sintaxis Moderna)    |
//+------------------------------------------------------------------+
input group "=== GESTION DE RIESGO Y CAPITAL ==="
input ENUM_RISK_MODE InpRiskMode             = RISK_PERCENT; // Modo de calculo de lote
input double         InpRiskPercent          = 1.0;          // Porcentaje de riesgo por operacion (%)
input double         InpFixedLot             = 0.01;         // Volumen fijo (si se usa Lote Fijo)
input int            InpMaxOpenPositions     = 1;            // Maximo de posiciones abiertas simultaneas
input int            InpMaxSpreadPoints      = 35;           // Spread maximo permitido (en puntos)
input ulong          InpSlippagePoints       = 10;           // Desviacion maxima de ejecucion (Slippage)

input group "=== TIME & PRICE / KILLZONES ==="
input bool           InpUseTimeFilter        = true;         // Activar filtro de sesiones horarias
input bool           InpRequireAsianRange    = true;         // Exigir formacion previa de Rango Asiatico
input int            InpAsianStartHour       = 0;            // Rango Asiatico: Hora inicio (Broker)
input int            InpAsianStartMin        = 0;            // Rango Asiatico: Minuto inicio
input int            InpAsianEndHour         = 6;            // Rango Asiatico: Hora fin (Broker)
input int            InpAsianEndMin          = 0;            // Rango Asiatico: Minuto fin

input bool           InpTradeLondon          = true;         // Operar London Killzone
input int            InpLondonStartHour      = 7;            // Londres: Hora inicio (Broker)
input int            InpLondonStartMin       = 0;            // Londres: Minuto inicio
input int            InpLondonEndHour        = 11;           // Londres: Hora fin (Broker)
input int            InpLondonEndMin         = 0;            // Londres: Minuto fin

input bool           InpTradeNewYork         = true;         // Operar New York Killzone
input int            InpNYStartHour          = 12;           // Nueva York: Hora inicio (Broker)
input int            InpNYStartMin           = 0;            // Nueva York: Minuto inicio
input int            InpNYEndHour            = 17;           // Nueva York: Hora fin (Broker)
input int            InpNYEndMin             = 0;            // Nueva York: Minuto fin

input group "=== REGLAS ESTRATEGICAS ICT ==="
input bool           InpUseTrendFilter       = true;         // Filtrar direccion por Macro EMA
input int            InpEmaPeriod            = 200;          // Periodo de EMA Macro de tendencia
input ENUM_TIMEFRAMES InpEmaTimeframe        = PERIOD_CURRENT; // Timeframe de la EMA Macro
input int            InpSwingLookback        = 3;            // Barras a izq/der para Swing High/Low (MSS)
input int            InpMinFvgPoints         = 15;           // Tamano minimo del FVG en puntos
input ENUM_ENTRY_MODE InpEntryMode           = ENTRY_FVG_CE_50; // Nivel de mitigacion para entrada
input int            InpMaxFvgAgeBars        = 25;           // Validez maxima del FVG en barras
input double         InpMinMssBodyPercent    = 45.0;         // Porcentaje minimo del cuerpo en vela MSS (%)

input group "=== SALIDAS Y GESTION DE POSICION ==="
input double         InpRiskRewardRatio      = 2.0;          // Ratio Riesgo/Beneficio (R:R)
input int            InpSlBufferPoints       = 20;           // Margen de seguridad del SL (puntos)
input int            InpMinSlPoints          = 40;           // SL minimo de seguridad (puntos)
input int            InpMaxSlPoints          = 600;          // SL maximo permitido (puntos)

input bool           InpUseBreakEven         = true;         // Activar Break Even automatico
input double         InpBeTriggerRR          = 1.0;          // Activar BE al alcanzar este R:R (ej: 1.0 = 1R)
input int            InpBeLockProfitPoints   = 5;            // Ganancia asegurada al pasar a BE (puntos)

input bool           InpUseTrailingStop      = false;        // Activar Trailing Stop dinamico
input int            InpTrailingStartPoints  = 100;          // Puntos de ganancia para iniciar Trailing
input int            InpTrailingDistance     = 60;           // Distancia del Trailing (puntos)
input int            InpTrailingStep         = 15;           // Paso de modificacion del Trailing (puntos)

input group "=== CONFIGURACION GENERAL Y GRAFICO ==="
input ulong          InpMagicNumber          = 1082026;      // Magic Number unico del Asesor Experto
input string         InpTradeComment         = "ICT_EA_v2";  // Comentario de orden
input bool           InpDrawZones            = true;         // Dibujar visualmente cajas FVG y Rango
input color          InpColorAsianBox        = C'180,180,220'; // Color caja Rango Asiatico
input color          InpColorBullFvg         = C'46,139,87';   // Color FVG Alcista
input color          InpColorBearFvg         = C'205,92,92';   // Color FVG Bajista

//+------------------------------------------------------------------+
//| Estructuras de Datos Internas                                    |
//+------------------------------------------------------------------+
struct SFairValueGap
{
   bool              active;
   bool              isBullish;
   double            highPrice;
   double            lowPrice;
   double            cePrice;          // Consequent Encroachment (50%)
   datetime          time;
   int               barIndex;
   string            objName;
};

struct SAsianRange
{
   bool              isDefined;
   datetime          sessionDate;
   double            high;
   double            low;
   bool              sweptHigh;
   bool              sweptLow;
};

//+------------------------------------------------------------------+
//| Instancias Globales                                              |
//+------------------------------------------------------------------+
CTrade               m_trade;
CSymbolInfo          m_symbol;
CPositionInfo        m_position;
CAccountInfo         m_account;

int                  m_emaHandle          = INVALID_HANDLE;
datetime             m_lastBarTime        = 0;
SAsianRange          m_asianRange;
SFairValueGap        m_activeFvg;

#define PREFIX_OBJ   "ICT_EA_"

//+------------------------------------------------------------------+
//| Prototipos de Funciones Auxiliares                               |
//+------------------------------------------------------------------+
bool   CheckNewBar();
int    CountOpenPositions();
void   ResetAsianRange();
void   ResetActiveFvg();
void   UpdateSessionsAndRanges();
bool   IsInTradeSession();
int    GetMacroTrendDirection();
void   ScanMarketStructureAndFvg();
void   CheckFvgEntryMitigation();
double CalculateLotSize(double slDistancePrice);
double NormalizeVolume(double volume);
void   ManageOpenPositions();
double FindRecentSwingHigh(int startBar, int maxLookback, int swingBars);
double FindRecentSwingLow(int startBar, int maxLookback, int swingBars);
void   DrawAsianRangeBox(datetime timeStart, datetime timeEnd, double high, double low);
void   DrawFvgBox(string name, datetime timeStart, double priceHigh, double priceLow, color clr);
void   DeleteAllVisualObjects();

//+------------------------------------------------------------------+
//| Funcion de Inicializacion del Asesor Experto                     |
//+------------------------------------------------------------------+
int OnInit()
{
   // Inicializar informacion del simbolo
   if(!m_symbol.Name(_Symbol))
   {
      Print("[ERROR] No se pudo inicializar la informacion del simbolo: ", _Symbol);
      return INIT_FAILED;
   }
   m_symbol.Refresh();

   // Configurar el gestor de ejecucion CTrade
   m_trade.SetExpertMagicNumber(InpMagicNumber);
   m_trade.SetDeviationInPoints(InpSlippagePoints);
   m_trade.SetMarginMode();
   m_trade.SetTypeFillingBySymbol(m_symbol.Name());

   // Inicializar indicador EMA si el filtro esta activo
   if(InpUseTrendFilter)
   {
      m_emaHandle = iMA(m_symbol.Name(), InpEmaTimeframe, InpEmaPeriod, 0, MODE_EMA, PRICE_CLOSE);
      if(m_emaHandle == INVALID_HANDLE)
      {
         Print("[ERROR] Error al crear el manejador de la EMA ", InpEmaPeriod);
         return INIT_FAILED;
      }
   }

   // Inicializar estructuras
   ResetAsianRange();
   ResetActiveFvg();

   Print("[INICIADO] ICT Strategy EA cargado con exito en ", _Symbol, " | TF: ", EnumToString(_Period), " | Magic: ", InpMagicNumber);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Funcion de Desinicializacion del Asesor Experto                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(m_emaHandle != INVALID_HANDLE)
   {
      IndicatorRelease(m_emaHandle);
      m_emaHandle = INVALID_HANDLE;
   }

   // Limpiar objetos visuales creados por el EA
   if(InpDrawZones)
   {
      DeleteAllVisualObjects();
      ChartRedraw(0);
   }

   Print("[DESCARGADO] ICT Strategy EA finalizado. Motivo: ", reason);
}

//+------------------------------------------------------------------+
//| Evento Principal OnTick                                          |
//+------------------------------------------------------------------+
void OnTick()
{
   // 1. Refrescar datos de mercado
   if(!m_symbol.RefreshRates())
      return;

   // 2. Gestion de posiciones abiertas (Trailing Stop & Break Even por tick)
   ManageOpenPositions();

   // 3. Control de Nueva Barra para logica de deteccion y evaluacion
   bool isNewBar = CheckNewBar();

   // 4. Actualizar estado del Rango Asiatico y Killzones
   UpdateSessionsAndRanges();

   // 5. Validar si ya tenemos el cupo maximo de posiciones abiertas
   if(CountOpenPositions() >= InpMaxOpenPositions)
      return;

   // 6. Validar filtro de spread
   if(m_symbol.Spread() > InpMaxSpreadPoints)
      return;

   // 7. En cada nueva barra, buscar nuevos patrones de Sweep, MSS y FVG
   if(isNewBar)
   {
      ScanMarketStructureAndFvg();
   }

   // 8. Monitorear ejecucion de entrada si tenemos un FVG pendiente
   CheckFvgEntryMitigation();
}

//+------------------------------------------------------------------+
//| Verifica si ha abierto una nueva barra en el timeframe actual    |
//+------------------------------------------------------------------+
bool CheckNewBar()
{
   datetime currentBarTime = iTime(m_symbol.Name(), _Period, 0);
   if(currentBarTime == 0)
      return false;

   if(currentBarTime != m_lastBarTime)
   {
      m_lastBarTime = currentBarTime;
      return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| Conteo de posiciones abiertas pertenecientes a este EA           |
//+------------------------------------------------------------------+
int CountOpenPositions()
{
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(m_position.SelectByIndex(i))
      {
         if(m_position.Symbol() == m_symbol.Name() && m_position.Magic() == InpMagicNumber)
         {
            count++;
         }
      }
   }
   return count;
}

//+------------------------------------------------------------------+
//| Reinicia el estado del Rango Asiatico                            |
//+------------------------------------------------------------------+
void ResetAsianRange()
{
   m_asianRange.isDefined    = false;
   m_asianRange.sessionDate = 0;
   m_asianRange.high        = 0.0;
   m_asianRange.low         = 0.0;
   m_asianRange.sweptHigh   = false;
   m_asianRange.sweptLow    = false;
}

//+------------------------------------------------------------------+
//| Reinicia el estado del FVG activo                                |
//+------------------------------------------------------------------+
void ResetActiveFvg()
{
   m_activeFvg.active           = false;
   m_activeFvg.isBullish        = false;
   m_activeFvg.highPrice        = 0.0;
   m_activeFvg.lowPrice         = 0.0;
   m_activeFvg.cePrice          = 0.0;
   m_activeFvg.time             = 0;
   m_activeFvg.barIndex         = 0;
   m_activeFvg.objName          = "";
}

//+------------------------------------------------------------------+
//| Actualiza los rangos horarios, Asian High/Low y barridos         |
//+------------------------------------------------------------------+
void UpdateSessionsAndRanges()
{
   datetime now = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(now, dt);

   int currentMinutesOfDay = dt.hour * 60 + dt.min;
   int asianStartMinutes   = InpAsianStartHour * 60 + InpAsianStartMin;
   int asianEndMinutes     = InpAsianEndHour * 60 + InpAsianEndMin;

   // Definir fecha del dia actual a las 00:00
   datetime todayMidnight = now - (currentMinutesOfDay * 60 + dt.sec);

   // Nuevo dia: reiniciar rango si cambio la fecha
   if(m_asianRange.sessionDate != todayMidnight)
   {
      ResetAsianRange();
      m_asianRange.sessionDate = todayMidnight;
   }

   // 1. Fase de Acumulacion: Durante la sesion asiatica, calcular maximos y minimos
   if(currentMinutesOfDay >= asianStartMinutes && currentMinutesOfDay <= asianEndMinutes)
   {
      double currentHigh = iHigh(m_symbol.Name(), _Period, 0);
      double currentLow  = iLow(m_symbol.Name(), _Period, 0);

      if(!m_asianRange.isDefined)
      {
         m_asianRange.high      = currentHigh;
         m_asianRange.low       = currentLow;
         m_asianRange.isDefined = true;
      }
      else
      {
         if(currentHigh > m_asianRange.high) m_asianRange.high = currentHigh;
         if(currentLow < m_asianRange.low && currentLow > 0.0) m_asianRange.low = currentLow;
      }

      if(InpDrawZones)
      {
         DrawAsianRangeBox(m_asianRange.sessionDate + (asianStartMinutes * 60),
                           m_asianRange.sessionDate + (asianEndMinutes * 60),
                           m_asianRange.high,
                           m_asianRange.low);
      }
   }

   // 2. Monitorear barridos de liquidez del Asian High / Asian Low
   if(m_asianRange.isDefined && currentMinutesOfDay > asianEndMinutes)
   {
      double ask = m_symbol.Ask();
      double bid = m_symbol.Bid();

      if(!m_asianRange.sweptHigh && bid > m_asianRange.high)
      {
         m_asianRange.sweptHigh = true;
         Print("[ICT SWEEP] Barrido de Liquidez de compras (Asian High) detectado en: ", bid);
      }

      if(!m_asianRange.sweptLow && ask < m_asianRange.low)
      {
         m_asianRange.sweptLow = true;
         Print("[ICT SWEEP] Barrido de Liquidez de ventas (Asian Low) detectado en: ", ask);
      }
   }
}

//+------------------------------------------------------------------+
//| Determina si el momento actual esta dentro de una Killzone valida|
//+------------------------------------------------------------------+
bool IsInTradeSession()
{
   if(!InpUseTimeFilter)
      return true;

   datetime now = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(now, dt);

   int currentMinutes = dt.hour * 60 + dt.min;

   // London Killzone
   if(InpTradeLondon)
   {
      int start = InpLondonStartHour * 60 + InpLondonStartMin;
      int end   = InpLondonEndHour * 60 + InpLondonEndMin;
      if(currentMinutes >= start && currentMinutes <= end)
         return true;
   }

   // New York Killzone
   if(InpTradeNewYork)
   {
      int start = InpNYStartHour * 60 + InpNYStartMin;
      int end   = InpNYEndHour * 60 + InpNYEndMin;
      if(currentMinutes >= start && currentMinutes <= end)
         return true;
   }

   return false;
}

//+------------------------------------------------------------------+
//| Evalua la direccion de la tendencia con la EMA Macro             |
//+------------------------------------------------------------------+
int GetMacroTrendDirection()
{
   if(!InpUseTrendFilter || m_emaHandle == INVALID_HANDLE)
      return 0; // Neutro / Sin filtro

   double emaValues[1];
   if(CopyBuffer(m_emaHandle, 0, 1, 1, emaValues) <= 0)
      return 0;

   double closePrice = iClose(m_symbol.Name(), _Period, 1);
   if(closePrice > emaValues[0])
      return 1;  // Tendencia Alcista
   else if(closePrice < emaValues[0])
      return -1; // Tendencia Bajista

   return 0;
}

//+------------------------------------------------------------------+
//| Escaneo de Estructura: Detecta Swing Points, MSS y nuevo FVG     |
//+------------------------------------------------------------------+
void ScanMarketStructureAndFvg()
{
   // Si no estamos en Killzone, no buscamos nuevos setups
   if(!IsInTradeSession())
      return;

   // Si ya tenemos un FVG activo esperando entrada, verificar su vigencia en barras
   if(m_activeFvg.active)
   {
      int barsSinceCreation = iBarShift(m_symbol.Name(), _Period, m_activeFvg.time);
      if(barsSinceCreation > InpMaxFvgAgeBars)
      {
         Print("[ICT FVG] El FVG activo expiro sin mitigacion tras ", barsSinceCreation, " barras.");
         ResetActiveFvg();
      }
   }

   // Se analiza la barra recien cerrada (indice 1)
   // Patron FVG de 3 barras: barra 3, barra 2 (desplazamiento) y barra 1
   double high1 = iHigh(m_symbol.Name(), _Period, 1);
   double low1  = iLow(m_symbol.Name(), _Period, 1);
   double open2 = iOpen(m_symbol.Name(), _Period, 2);
   double close2= iClose(m_symbol.Name(), _Period, 2);
   double high2 = iHigh(m_symbol.Name(), _Period, 2);
   double low2  = iLow(m_symbol.Name(), _Period, 2);
   double high3 = iHigh(m_symbol.Name(), _Period, 3);
   double low3  = iLow(m_symbol.Name(), _Period, 3);

   double range2 = high2 - low2;
   double body2  = MathAbs(close2 - open2);
   if(range2 <= 0.0)
      return;

   // Desplazamiento minimo: la vela central 2 debe tener cuerpo institucional
   double bodyPercent = (body2 / range2) * 100.0;
   if(bodyPercent < InpMinMssBodyPercent)
      return;

   int trend = GetMacroTrendDirection();

   // ---------------------------------------------------------------
   // CASO ALCISTA: Bullish FVG + Bullish MSS
   // ---------------------------------------------------------------
   if(low1 > high3) // Existe vacio de liquidez entre barra 1 y barra 3
   {
      double fvgSizePoints = (low1 - high3) / m_symbol.Point();
      if(fvgSizePoints >= InpMinFvgPoints && close2 > open2)
      {
         // Filtro de Macro Tendencia
         if(InpUseTrendFilter && trend < 0)
            return;

         // Filtro de barrido asiatico previo (si esta configurado)
         if(InpRequireAsianRange && m_asianRange.isDefined && !m_asianRange.sweptLow)
            return;

         // Validar Market Structure Shift (MSS):
         // La vela 2 debe haber roto con cuerpo el swing high previo mas reciente
         double recentSwingHigh = FindRecentSwingHigh(3, 30, InpSwingLookback);
         if(recentSwingHigh > 0.0 && close2 > recentSwingHigh)
         {
            m_activeFvg.active           = true;
            m_activeFvg.isBullish        = true;
            m_activeFvg.highPrice        = low1;
            m_activeFvg.lowPrice         = high3;
            m_activeFvg.cePrice          = (low1 + high3) / 2.0;
            m_activeFvg.time             = iTime(m_symbol.Name(), _Period, 1);
            m_activeFvg.barIndex         = 1;
            m_activeFvg.objName          = PREFIX_OBJ + "BULL_FVG_" + TimeToString(m_activeFvg.time);

            PrintFormat("[ICT SETUP ALCISTA] MSS confirmado en %.5f con Bullish FVG: High=%.5f, Low=%.5f, CE=%.5f (Puntos: %.0f)",
                        recentSwingHigh, m_activeFvg.highPrice, m_activeFvg.lowPrice, m_activeFvg.cePrice, fvgSizePoints);

            if(InpDrawZones)
            {
               DrawFvgBox(m_activeFvg.objName, m_activeFvg.time, m_activeFvg.highPrice, m_activeFvg.lowPrice, InpColorBullFvg);
            }
         }
      }
   }

   // ---------------------------------------------------------------
   // CASO BAJISTA: Bearish FVG + Bearish MSS
   // ---------------------------------------------------------------
   if(high1 < low3) // Existe vacio de liquidez entre barra 3 y barra 1
   {
      double fvgSizePoints = (low3 - high1) / m_symbol.Point();
      if(fvgSizePoints >= InpMinFvgPoints && close2 < open2)
      {
         // Filtro de Macro Tendencia
         if(InpUseTrendFilter && trend > 0)
            return;

         // Filtro de barrido asiatico previo (si esta configurado)
         if(InpRequireAsianRange && m_asianRange.isDefined && !m_asianRange.sweptHigh)
            return;

         // Validar Market Structure Shift (MSS):
         // La vela 2 debe haber roto con cuerpo el swing low previo mas reciente
         double recentSwingLow = FindRecentSwingLow(3, 30, InpSwingLookback);
         if(recentSwingLow > 0.0 && close2 < recentSwingLow)
         {
            m_activeFvg.active           = true;
            m_activeFvg.isBullish        = false;
            m_activeFvg.highPrice        = low3;
            m_activeFvg.lowPrice         = high1;
            m_activeFvg.cePrice          = (low3 + high1) / 2.0;
            m_activeFvg.time             = iTime(m_symbol.Name(), _Period, 1);
            m_activeFvg.barIndex         = 1;
            m_activeFvg.objName          = PREFIX_OBJ + "BEAR_FVG_" + TimeToString(m_activeFvg.time);

            PrintFormat("[ICT SETUP BAJISTA] MSS confirmado en %.5f con Bearish FVG: High=%.5f, Low=%.5f, CE=%.5f (Puntos: %.0f)",
                        recentSwingLow, m_activeFvg.highPrice, m_activeFvg.lowPrice, m_activeFvg.cePrice, fvgSizePoints);

            if(InpDrawZones)
            {
               DrawFvgBox(m_activeFvg.objName, m_activeFvg.time, m_activeFvg.highPrice, m_activeFvg.lowPrice, InpColorBearFvg);
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Monitorea el retroceso del precio hacia el FVG y ejecuta entrada |
//+------------------------------------------------------------------+
void CheckFvgEntryMitigation()
{
   if(!m_activeFvg.active)
      return;

   // Solo se opera si estamos en Killzone
   if(!IsInTradeSession())
      return;

   double ask = m_symbol.Ask();
   double bid = m_symbol.Bid();

   // --- ENTRADA EN COMPRA (BULLISH FVG) ---
   if(m_activeFvg.isBullish)
   {
      double triggerPrice = (InpEntryMode == ENTRY_FVG_CE_50) ? m_activeFvg.cePrice : m_activeFvg.highPrice;

      // Si el precio retrocede hacia la zona de compra
      if(ask <= triggerPrice && ask >= m_activeFvg.lowPrice)
      {
         // Stop Loss: por debajo del minimo del FVG o del swing bajo reciente + buffer
         double swingLow = FindRecentSwingLow(1, 15, 2);
         double baseLow  = (swingLow > 0.0) ? MathMin(m_activeFvg.lowPrice, swingLow) : m_activeFvg.lowPrice;
         double slPrice  = baseLow - (InpSlBufferPoints * m_symbol.Point());

         // Validar distancias de SL
         double slDistPoints = (ask - slPrice) / m_symbol.Point();
         if(slDistPoints < InpMinSlPoints)
            slPrice = ask - (InpMinSlPoints * m_symbol.Point());
         if(slDistPoints > InpMaxSlPoints)
            slPrice = ask - (InpMaxSlPoints * m_symbol.Point());

         double finalSlDist = ask - slPrice;
         double tpPrice     = ask + (finalSlDist * InpRiskRewardRatio);

         // Normalizar precios
         slPrice = m_symbol.NormalizePrice(slPrice);
         tpPrice = m_symbol.NormalizePrice(tpPrice);

         // Calcular lote segun riesgo
         double lotSize = CalculateLotSize(ask - slPrice);
         if(lotSize <= 0.0)
         {
            Print("[ERROR] Lote calculado invalido para Buy: ", lotSize);
            return;
         }

         // Enviar orden de compra
         if(m_trade.Buy(lotSize, m_symbol.Name(), ask, slPrice, tpPrice, InpTradeComment))
         {
            PrintFormat("[ICT EJECUCION BUY] Lote=%.2f, Entrada=%.5f, SL=%.5f, TP=%.5f, R:R=1:%.1f",
                        lotSize, ask, slPrice, tpPrice, InpRiskRewardRatio);
            ResetActiveFvg();
         }
         else
         {
            Print("[ERROR] Fallo al abrir Buy: ", m_trade.ResultRetcodeDescription());
         }
      }
      else if(bid < m_activeFvg.lowPrice)
      {
         // FVG invalidado si el precio perfora completamente por debajo
         Print("[ICT FVG] Bullish FVG invalidado por perforacion a la baja.");
         ResetActiveFvg();
      }
   }
   // --- ENTRADA EN VENTA (BEARISH FVG) ---
   else
   {
      double triggerPrice = (InpEntryMode == ENTRY_FVG_CE_50) ? m_activeFvg.cePrice : m_activeFvg.lowPrice;

      // Si el precio retrocede hacia la zona de venta
      if(bid >= triggerPrice && bid <= m_activeFvg.highPrice)
      {
         // Stop Loss: por encima del maximo del FVG o del swing alto reciente + buffer
         double swingHigh = FindRecentSwingHigh(1, 15, 2);
         double baseHigh  = (swingHigh > 0.0) ? MathMax(m_activeFvg.highPrice, swingHigh) : m_activeFvg.highPrice;
         double slPrice   = baseHigh + (InpSlBufferPoints * m_symbol.Point());

         // Validar distancias de SL
         double slDistPoints = (slPrice - bid) / m_symbol.Point();
         if(slDistPoints < InpMinSlPoints)
            slPrice = bid + (InpMinSlPoints * m_symbol.Point());
         if(slDistPoints > InpMaxSlPoints)
            slPrice = bid + (InpMaxSlPoints * m_symbol.Point());

         double finalSlDist = slPrice - bid;
         double tpPrice     = bid - (finalSlDist * InpRiskRewardRatio);

         // Normalizar precios
         slPrice = m_symbol.NormalizePrice(slPrice);
         tpPrice = m_symbol.NormalizePrice(tpPrice);

         // Calcular lote segun riesgo
         double lotSize = CalculateLotSize(slPrice - bid);
         if(lotSize <= 0.0)
         {
            Print("[ERROR] Lote calculado invalido para Sell: ", lotSize);
            return;
         }

         // Enviar orden de venta
         if(m_trade.Sell(lotSize, m_symbol.Name(), bid, slPrice, tpPrice, InpTradeComment))
         {
            PrintFormat("[ICT EJECUCION SELL] Lote=%.2f, Entrada=%.5f, SL=%.5f, TP=%.5f, R:R=1:%.1f",
                        lotSize, bid, slPrice, tpPrice, InpRiskRewardRatio);
            ResetActiveFvg();
         }
         else
         {
            Print("[ERROR] Fallo al abrir Sell: ", m_trade.ResultRetcodeDescription());
         }
      }
      else if(ask > m_activeFvg.highPrice)
      {
         // FVG invalidado si el precio perfora completamente por encima
         Print("[ICT FVG] Bearish FVG invalidado por perforacion al alza.");
         ResetActiveFvg();
      }
   }
}

//+------------------------------------------------------------------+
//| Calcula el tamano de lote dinamico segun riesgo porcentual       |
//+------------------------------------------------------------------+
double CalculateLotSize(double slDistancePrice)
{
   if(InpRiskMode == RISK_FIXED_LOT)
   {
      return NormalizeVolume(InpFixedLot);
   }

   if(slDistancePrice <= 0.0)
      return 0.0;

   double balance       = m_account.Balance();
   double riskMoney     = balance * (InpRiskPercent / 100.0);
   double tickSize      = m_symbol.TickSize();
   double tickValue     = m_symbol.TickValue();

   if(tickSize <= 0.0 || tickValue <= 0.0)
   {
      // Estimacion de respaldo si el broker aun no ha retornado tick value
      return NormalizeVolume(InpFixedLot);
   }

   double slTicks       = slDistancePrice / tickSize;
   double moneyPerLot   = slTicks * tickValue;

   if(moneyPerLot <= 0.0)
      return NormalizeVolume(InpFixedLot);

   double calculatedLot = riskMoney / moneyPerLot;
   return NormalizeVolume(calculatedLot);
}

//+------------------------------------------------------------------+
//| Normaliza el volumen segun los limites y pasos del simbolo       |
//+------------------------------------------------------------------+
double NormalizeVolume(double volume)
{
   double minLot  = m_symbol.LotsMin();
   double maxLot  = m_symbol.LotsMax();
   double stepLot = m_symbol.LotsStep();

   if(stepLot <= 0.0)
      stepLot = 0.01;

   double normalized = MathFloor(volume / stepLot) * stepLot;

   if(normalized < minLot) normalized = minLot;
   if(normalized > maxLot) normalized = maxLot;

   int digits = 2;
   if(stepLot == 0.1)   digits = 1;
   if(stepLot == 1.0)   digits = 0;
   if(stepLot == 0.001) digits = 3;

   return NormalizeDouble(normalized, digits);
}

//+------------------------------------------------------------------+
//| Gestiona Break Even y Trailing Stop de posiciones abiertas       |
//+------------------------------------------------------------------+
void ManageOpenPositions()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(!m_position.SelectByIndex(i))
         continue;

      if(m_position.Symbol() != m_symbol.Name() || m_position.Magic() != InpMagicNumber)
         continue;

      ulong  ticket       = m_position.Ticket();
      double openPrice    = m_position.PriceOpen();
      double currentSL    = m_position.StopLoss();
      double currentTP    = m_position.TakeProfit();
      double currentPrice = m_position.PriceCurrent();
      ENUM_POSITION_TYPE posType = m_position.PositionType();

      // Distancia inicial de riesgo (1R)
      double riskDistance = MathAbs(openPrice - currentSL);
      if(riskDistance <= 0.0)
         continue;

      // -------------------------------------------------------------
      // 1. GESTION DE BREAK EVEN
      // -------------------------------------------------------------
      if(InpUseBreakEven)
      {
         double profitDistance = (posType == POSITION_TYPE_BUY) ? (currentPrice - openPrice) : (openPrice - currentPrice);
         double targetDistance = riskDistance * InpBeTriggerRR;

         if(profitDistance >= targetDistance)
         {
            if(posType == POSITION_TYPE_BUY)
            {
               double bePrice = m_symbol.NormalizePrice(openPrice + (InpBeLockProfitPoints * m_symbol.Point()));
               if(currentSL < openPrice) // Solo modificar si no estaba ya en ganancia
               {
                  if(m_trade.PositionModify(ticket, bePrice, currentTP))
                  {
                     PrintFormat("[BREAK EVEN] Posicion #%d movida a BE (+%.0f pts)", ticket, (double)InpBeLockProfitPoints);
                  }
               }
            }
            else if(posType == POSITION_TYPE_SELL)
            {
               double bePrice = m_symbol.NormalizePrice(openPrice - (InpBeLockProfitPoints * m_symbol.Point()));
               if(currentSL > openPrice || currentSL == 0.0)
               {
                  if(m_trade.PositionModify(ticket, bePrice, currentTP))
                  {
                     PrintFormat("[BREAK EVEN] Posicion #%d movida a BE (+%.0f pts)", ticket, (double)InpBeLockProfitPoints);
                  }
               }
            }
         }
      }

      // -------------------------------------------------------------
      // 2. GESTION DE TRAILING STOP
      // -------------------------------------------------------------
      if(InpUseTrailingStop)
      {
         double startPointsDist    = InpTrailingStartPoints * m_symbol.Point();
         double trailingPointsDist = InpTrailingDistance * m_symbol.Point();
         double trailingStepDist   = InpTrailingStep * m_symbol.Point();

         if(posType == POSITION_TYPE_BUY)
         {
            if(currentPrice - openPrice >= startPointsDist)
            {
               double newSL = m_symbol.NormalizePrice(currentPrice - trailingPointsDist);
               if(newSL > currentSL + trailingStepDist)
               {
                  m_trade.PositionModify(ticket, newSL, currentTP);
               }
            }
         }
         else if(posType == POSITION_TYPE_SELL)
         {
            if(openPrice - currentPrice >= startPointsDist)
            {
               double newSL = m_symbol.NormalizePrice(currentPrice + trailingPointsDist);
               if(newSL < currentSL - trailingStepDist || currentSL == 0.0)
               {
                  m_trade.PositionModify(ticket, newSL, currentTP);
               }
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Encuentra el Swing High fractal mas reciente                     |
//+------------------------------------------------------------------+
double FindRecentSwingHigh(int startBar, int maxLookback, int swingBars)
{
   int firstBar = (int)MathMax(startBar, swingBars + 1);
   for(int i = firstBar; i <= firstBar + maxLookback; i++)
   {
      double candidate = iHigh(m_symbol.Name(), _Period, i);
      if(candidate <= 0.0) continue;
      bool isHigh = true;

      for(int k = 1; k <= swingBars; k++)
      {
         double leftBarHigh  = iHigh(m_symbol.Name(), _Period, i + k);
         double rightBarHigh = iHigh(m_symbol.Name(), _Period, i - k);
         if(leftBarHigh >= candidate || rightBarHigh >= candidate)
         {
            isHigh = false;
            break;
         }
      }

      if(isHigh)
         return candidate;
   }
   return 0.0;
}

//+------------------------------------------------------------------+
//| Encuentra el Swing Low fractal mas reciente                      |
//+------------------------------------------------------------------+
double FindRecentSwingLow(int startBar, int maxLookback, int swingBars)
{
   int firstBar = (int)MathMax(startBar, swingBars + 1);
   for(int i = firstBar; i <= firstBar + maxLookback; i++)
   {
      double candidate = iLow(m_symbol.Name(), _Period, i);
      if(candidate <= 0.0) continue;
      bool isLow = true;

      for(int k = 1; k <= swingBars; k++)
      {
         double leftBarLow  = iLow(m_symbol.Name(), _Period, i + k);
         double rightBarLow = iLow(m_symbol.Name(), _Period, i - k);
         if(leftBarLow <= candidate || rightBarLow <= candidate)
         {
            isLow = false;
            break;
         }
      }

      if(isLow)
         return candidate;
   }
   return 0.0;
}

//+------------------------------------------------------------------+
//| Dibuja la caja del Rango Asiatico en el grafico                  |
//+------------------------------------------------------------------+
void DrawAsianRangeBox(datetime timeStart, datetime timeEnd, double high, double low)
{
   string name = PREFIX_OBJ + "ASIAN_RANGE_" + TimeToString(timeStart, TIME_DATE);

   if(ObjectFind(0, name) < 0)
   {
      ObjectCreate(0, name, OBJ_RECTANGLE, 0, timeStart, high, timeEnd, low);
      ObjectSetInteger(0, name, OBJPROP_COLOR, InpColorAsianBox);
      ObjectSetInteger(0, name, OBJPROP_STYLE, STYLE_DASH);
      ObjectSetInteger(0, name, OBJPROP_WIDTH, 1);
      ObjectSetInteger(0, name, OBJPROP_BACK, true);
      ObjectSetInteger(0, name, OBJPROP_FILL, false);
      ObjectSetString(0, name, OBJPROP_TOOLTIP, "Rango Asiatico ICT (Acumulacion)");
   }
   else
   {
      ObjectSetDouble(0, name, OBJPROP_PRICE, 0, high);
      ObjectSetDouble(0, name, OBJPROP_PRICE, 1, low);
      ObjectSetInteger(0, name, OBJPROP_TIME, 1, timeEnd);
   }
}

//+------------------------------------------------------------------+
//| Dibuja la zona de Fair Value Gap en el grafico                   |
//+------------------------------------------------------------------+
void DrawFvgBox(string name, datetime timeStart, double priceHigh, double priceLow, color clr)
{
   datetime timeEnd = timeStart + (PeriodSeconds(_Period) * 10);

   if(ObjectFind(0, name) < 0)
   {
      ObjectCreate(0, name, OBJ_RECTANGLE, 0, timeStart, priceHigh, timeEnd, priceLow);
      ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
      ObjectSetInteger(0, name, OBJPROP_WIDTH, 1);
      ObjectSetInteger(0, name, OBJPROP_BACK, true);
      ObjectSetInteger(0, name, OBJPROP_FILL, true);
      ObjectSetString(0, name, OBJPROP_TOOLTIP, "ICT Fair Value Gap (FVG)");
   }
}

//+------------------------------------------------------------------+
//| Limpia los objetos visuales creados por el EA                    |
//+------------------------------------------------------------------+
void DeleteAllVisualObjects()
{
   for(int i = ObjectsTotal(0, 0, -1) - 1; i >= 0; i--)
   {
      string name = ObjectName(0, i, 0, -1);
      if(StringFind(name, PREFIX_OBJ) == 0)
      {
         ObjectDelete(0, name);
      }
   }
}
//+------------------------------------------------------------------+
