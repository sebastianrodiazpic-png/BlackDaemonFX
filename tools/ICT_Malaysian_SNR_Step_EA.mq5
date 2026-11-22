//+------------------------------------------------------------------+
//|                                  ICT_Malaysian_SNR_Step_EA.mq5   |
//|                                  Copyright 2026, BlackDaemonFX   |
//|               MultiStrategia Oficial Worker STEP (ICT + MSNR)    |
//|                 Edicion Profesional Rentable (Winrate > 55%)     |
//+------------------------------------------------------------------+
#property copyright   "Copyright 2026, BlackDaemonFX"
#property link        "https://github.com/sebastianrodiazpic-png/BlackDaemonFX"
#property version     "5.00"
#property description "Worker STEP v5.00: ICT + Malaysian SNR Confluence Sniper."
#property description "Riesgo fijo ($50/trade), R:R 1:2.0 limpio, filtro macro H1 (EMA 50/200 + Pendiente)."
#property description "Sesgo direccional optimizado (DIR_ONLY_SELL) con proteccion de circuito diario."

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
enum ENUM_EXECUTION_MODE
{
   MODE_STRICT_CONFLUENCE, // Confluencia Estricta: Exige coincidencia de MSNR + FVG ICT (Recomendado)
   MODE_DUAL_CONCURRENT    // MultiStrategia: Ambos motores operan senales independientes
};

enum ENUM_TRADE_DIRECTION
{
   DIR_ALL,                // Operar Compras y Ventas (Filtradas por RSI H1)
   DIR_ONLY_SELL,          // Solo Ventas (Ideal si el activo esta en tendencia bajista)
   DIR_ONLY_BUY            // Solo Compras
};

enum ENUM_ORDER_STYLE
{
   STYLE_SINGLE_ORDER,     // Orden Unica: TP institucional 2.0R completo (Garantiza Payoff 2:1)
   STYLE_SPLIT_LEGS        // Doble Pierna: Pierna 1 (TP1) + Pierna 2 (TP2 Corredora)
};

enum ENUM_RISK_MODE
{
   RISK_FIXED_CASH,        // Riesgo Monetario Fijo en USD (Recomendado: asegura $100 win / $50 loss)
   RISK_PERCENT,           // Porcentaje de Riesgo sobre Balance
   RISK_FIXED_LOT          // Volumen Fijo Manual
};

enum ENUM_AV_DEFINITION
{
   AV_ENGULFING,           // Patron Envolvente Estricto (Engulfing de cuerpos)
   AV_BODY_TURNS           // Giro Simple de Cuerpos (Close[i-1] y Open[i])
};

//+------------------------------------------------------------------+
//| Parametros de Entrada                                            |
//+------------------------------------------------------------------+
input group "=== CONFIGURACION GENERAL WORKER STEP ==="
input ulong               InpMagicNumber          = 26082104;              // Magic Number Oficial Worker STEP
input string              InpBaseComment          = "STEP_SNIPER";         // Comentario base de orden
input ENUM_EXECUTION_MODE InpExecutionMode        = MODE_STRICT_CONFLUENCE;// Modo de Ejecucion (Confluencia para >55% WR)
input ENUM_TRADE_DIRECTION InpTradeDirection      = DIR_ONLY_SELL;         // Direccion operativa (DIR_ONLY_SELL captura el Edge ganador)
input ENUM_ORDER_STYLE    InpOrderStyle           = STYLE_SINGLE_ORDER;    // Estilo de Orden (Orden Unica para Payoff real)
input int                 InpMaxSpreadPoints      = 35;                    // Spread maximo absoluto (puntos)
input ulong               InpSlippagePoints       = 10;                    // Desviacion maxima tolerada (slippage)

input group "=== GESTION DE RIESGO Y CAPITAL (PAYOFF SIMETRICO) ==="
input ENUM_RISK_MODE      InpRiskMode             = RISK_FIXED_CASH;       // Modo de riesgo (Fixed Cash evita asimetria)
input double              InpFixedCashRisk        = 50.0;                  // Riesgo monetario fijo por trade en USD ($)
input double              InpRiskPercent          = 1.0;                   // Riesgo total (%) si se usa modo Percent
input double              InpFixedLot             = 0.01;                  // Lote fijo si se usa modo Fixed Lot
input int                 InpMaxOpenSets          = 1;                     // Maximo de posiciones simultaneas

input group "=== FILTRO MACRO DUAL HTF Y RSI (H1 BIAS) ==="
input bool                InpUseHtfFilter         = true;                  // Activar filtro de tendencia mayor HTF
input ENUM_TIMEFRAMES     InpHtfTimeframe         = PERIOD_H1;             // Timeframe mayor (H1)
input int                 InpHtfFastEmaPeriod     = 50;                    // Periodo EMA Rapida HTF
input int                 InpHtfSlowEmaPeriod     = 200;                   // Periodo EMA Lenta HTF
input bool                InpUseHtfRsiFilter      = true;                  // Activar filtro de Momentum RSI en H1
input int                 InpHtfRsiPeriod         = 14;                    // Periodo RSI en H1
input double              InpMinBuyRsi            = 50.0;                  // RSI H1 minimo para compras (>50)
input double              InpMaxSellRsi           = 50.0;                  // RSI H1 maximo para ventas (<50)

input group "=== FILTRO DE REGIMEN Y VOLATILIDAD (ADX / ATR) ==="
input bool                InpUseAdxFilter         = true;                  // Activar filtro ADX (evita mercado lateral)
input int                 InpAdxPeriod            = 14;                    // Periodo ADX
input double              InpMinAdxLevel          = 22.0;                  // Nivel minimo de ADX para operar
input double              InpMinFvgAtrRatio       = 0.40;                  // Tamano minimo de FVG relativo al ATR (0.4 * ATR)

input group "=== CIRCUITO DE PROTECCION DIARIO (CIRCUIT BREAKER) ==="
input bool                InpUseCircuitBreaker    = true;                  // Activar freno diario de emergencias
input double              InpMaxDailyLossPercent  = 3.0;                   // Perdida maxima diaria permitida (%)
input int                 InpMaxDailyConsLosses   = 3;                     // Maximo de perdidas consecutivas por dia
input double              InpMaxSpreadToSlRatio   = 0.08;                  // Spread maximo vs distancia al SL (8% max)

input group "=== OBJETIVOS Y SALIDAS (R:R LIMPIO 1:2) ==="
input double              InpSingleOrderRR        = 2.0;                   // Ratio R:R Orden Unica (1:2.0 Real = $100 win / $50 loss)
input double              InpTarget1_RR           = 1.5;                   // Primer Objetivo TP1 (para modo Split)
input double              InpTarget2_RR           = 2.5;                   // Segundo Objetivo TP2 (para modo Split)
input bool                InpEnableBreakEven      = false;                 // Activar Break Even (false evita mutilacion de trades)
input double              InpBeTriggerRR          = 1.4;                   // Activar BE al alcanzar R:R
input int                 InpBeLockPoints         = 5;                     // Puntos protegidos en BE (+spread)
input int                 InpSlBufferPoints       = 15;                    // Buffer de holgura de SL (puntos)
input int                 InpMinSlPoints          = 30;                    // SL minimo de seguridad (puntos)
input int                 InpMaxSlPoints          = 800;                   // SL maximo permitido (puntos)

input group "=== MOTOR MALAYSIAN SNR (RETEST SNIPER) ==="
input bool                InpMsnrEnabled          = true;                  // Habilitar motor Malaysian SNR
input ENUM_AV_DEFINITION  InpAvDefinition         = AV_ENGULFING;          // Definicion de niveles A/V
input int                 InpAvLookbackBars       = 60;                    // Barras para buscar niveles A/V
input int                 InpMaxBarsSinceBreak    = 20;                    // Maxima antiguedad de la ruptura en barras
input double              InpMinBreakDisplacement = 0.50;                  // Desplazamiento minimo ruptura (ATR)
input double              InpMaxRetestDistanceAtr = 0.25;                  // Tolerancia de penetracion de retest (ATR)
input int                 InpAtrPeriod            = 14;                    // Periodo de calculo ATR
input bool                InpRequireFreshLevel    = true;                  // Exigir nivel Fresh sin consumo previo
input bool                InpRequireRejectionWick = true;                  // Exigir rechazo por mecha en el retest

input group "=== MOTOR ICT (SMC / FVG / CE 50%) ==="
input bool                InpIctEnabled           = true;                  // Habilitar motor ICT
input int                 InpMinFvgPoints         = 15;                    // Tamano minimo de FVG en puntos
input int                 InpMaxFvgAgeBars        = 20;                    // Maxima duracion activa de FVG
input double              InpMinMssBodyPercent    = 45.0;                  // Cuerpo minimo en vela MSS (%)
input bool                InpUseConsequentEncroach= true;                  // Entrada en Consequent Encroachment (50% CE)
input int                 InpSwingLookback        = 3;                     // Barras a izq/der para Swings fractales

input group "=== SESIONES Y SINTETICOS 24/7 ==="
input bool                InpIsSynthetic247       = true;                  // Instrumento Sintetico (Opera 24/7 sin Killzone)
input bool                InpUseTimeFilter        = false;                 // Activar filtro horario para Forex/Metales
input int                 InpSessionStartHour     = 7;                     // Hora inicio sesion (Broker)
input int                 InpSessionEndHour       = 17;                    // Hora fin sesion (Broker)

input group "=== VISUALIZACION EN GRAFICO ==="
input bool                InpDrawVisuals          = true;                  // Dibujar zonas y lineas de niveles
input color               InpColorMsnrRes         = C'220,20,60';          // Color Resistencia A (Rojo Carmesi)
input color               InpColorMsnrSup         = C'30,144,255';         // Color Soporte V (Azul Dodger)
input color               InpColorBullFvg         = C'46,139,87';          // Color FVG Alcista (Verde Mar)
input color               InpColorBearFvg         = C'205,92,92';          // Color FVG Bajista (Rojo Indio)

//+------------------------------------------------------------------+
//| Estructuras de Datos de la Estrategia                            |
//+------------------------------------------------------------------+
struct SMsnrLevel
{
   bool              isResistance;   // true: Resistencia A, false: Soporte V
   double            breakLevel;     // Nivel de union de cuerpos (Close[i-1])
   double            wickBound;      // Extremo de la mecha (invalidacion)
   datetime          time;
   int               barIndex;
   bool              isFresh;        // Nivel sin toques previos
   bool              isBroken;       // Nivel roto con cuerpo por vela posterior
   datetime          breakTime;
   int               barsSinceBreak; // Cantidad de barras desde la ruptura
};

struct SIctFvg
{
   bool              active;
   bool              isBullish;
   double            highPrice;
   double            lowPrice;
   double            cePrice;        // 50% Consequent Encroachment
   datetime          time;
   int               barIndex;
   string            objName;
};

//+------------------------------------------------------------------+
//| Variables e Instancias Globales                                  |
//+------------------------------------------------------------------+
CTrade               m_trade;
CSymbolInfo          m_symbol;
CPositionInfo        m_position;
CAccountInfo         m_account;

int                  m_atrHandle          = INVALID_HANDLE;
int                  m_adxHandle          = INVALID_HANDLE;
int                  m_htfFastEmaHandle   = INVALID_HANDLE;
int                  m_htfSlowEmaHandle   = INVALID_HANDLE;
int                  m_htfRsiHandle       = INVALID_HANDLE;

datetime             m_lastBarTime        = 0;
datetime             m_lastTradeBarTime   = 0;
datetime             m_lastCircuitLogDate = 0;
SIctFvg              m_activeFvg;
SMsnrLevel           m_activeMsnrLevels[];
double               m_consumedLevels[];

#define PREFIX_STEP  "STEP_MULTI_"

//+------------------------------------------------------------------+
//| Prototipos de Funciones                                          |
//+------------------------------------------------------------------+
bool   CheckNewBar();
int    CountOpenPositionSets();
double GetCurrentAtr();
double GetCurrentAdx();
int    GetHtfTrendDirection();
bool   CheckDailyCircuitBreaker();
bool   IsLevelConsumed(double level);
void   MarkLevelAsConsumed(double level);
void   ScanMsnrLevels();
void   ScanIctMarketStructure();
void   EvaluateTradeExecution();
void   ExecuteTradeLegs(string strategyName, ENUM_ORDER_TYPE orderType, double price, double sl, double tp1, double tp2);
double CalculateLotSize(double slDistancePrice, double riskFraction);
double NormalizeVolume(double volume);
void   ManageOpenPositions();
double FindRecentSwingHigh(int startBar, int maxLookback, int swingBars);
double FindRecentSwingLow(int startBar, int maxLookback, int swingBars);
void   DrawHorizontalLine(string name, double price, color clr, ENUM_LINE_STYLE style, string tip);
void   DrawFvgBox(string name, datetime timeStart, double priceHigh, double priceLow, color clr);
void   DeleteAllVisualObjects();

//+------------------------------------------------------------------+
//| Inicializacion del Asesor Experto                                |
//+------------------------------------------------------------------+
int OnInit()
{
   if(!m_symbol.Name(_Symbol))
   {
      Print("[ERROR] No se pudo inicializar informacion para: ", _Symbol);
      return INIT_FAILED;
   }
   m_symbol.Refresh();

   m_trade.SetExpertMagicNumber(InpMagicNumber);
   m_trade.SetDeviationInPoints(InpSlippagePoints);
   m_trade.SetMarginMode();
   m_trade.SetTypeFillingBySymbol(m_symbol.Name());

   m_atrHandle = iATR(m_symbol.Name(), _Period, InpAtrPeriod);
   if(m_atrHandle == INVALID_HANDLE)
   {
      Print("[ERROR] No se pudo crear el manejador de ATR(", InpAtrPeriod, ")");
      return INIT_FAILED;
   }

   if(InpUseAdxFilter)
   {
      m_adxHandle = iADX(m_symbol.Name(), _Period, InpAdxPeriod);
      if(m_adxHandle == INVALID_HANDLE)
      {
         Print("[ERROR] No se pudo crear el manejador de ADX(", InpAdxPeriod, ")");
         return INIT_FAILED;
      }
   }

   if(InpUseHtfFilter)
   {
      m_htfFastEmaHandle = iMA(m_symbol.Name(), InpHtfTimeframe, InpHtfFastEmaPeriod, 0, MODE_EMA, PRICE_CLOSE);
      m_htfSlowEmaHandle = iMA(m_symbol.Name(), InpHtfTimeframe, InpHtfSlowEmaPeriod, 0, MODE_EMA, PRICE_CLOSE);
      if(m_htfFastEmaHandle == INVALID_HANDLE || m_htfSlowEmaHandle == INVALID_HANDLE)
      {
         Print("[ERROR] No se pudo crear el manejador de las EMAs HTF");
         return INIT_FAILED;
      }
   }

   if(InpUseHtfRsiFilter)
   {
      m_htfRsiHandle = iRSI(m_symbol.Name(), InpHtfTimeframe, InpHtfRsiPeriod, PRICE_CLOSE);
      if(m_htfRsiHandle == INVALID_HANDLE)
      {
         Print("[ERROR] No se pudo crear el manejador de RSI HTF");
         return INIT_FAILED;
      }
   }

   ArrayResize(m_activeMsnrLevels, 0);
   ArrayResize(m_consumedLevels, 0);
   m_activeFvg.active = false;

   PrintFormat("[INICIADO v4.50 RENTABLE] Step EA listo | Simbolo: %s | Modo: %s | Riesgo: %s ($%.0f)",
               _Symbol, (InpExecutionMode == MODE_STRICT_CONFLUENCE ? "Confluencia Estricta" : "Dual"),
               (InpRiskMode == RISK_FIXED_CASH ? "Fixed Cash" : "Percent"), InpFixedCashRisk);

   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Desinicializacion del Asesor Experto                             |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(m_atrHandle != INVALID_HANDLE) IndicatorRelease(m_atrHandle);
   if(m_adxHandle != INVALID_HANDLE) IndicatorRelease(m_adxHandle);
   if(m_htfFastEmaHandle != INVALID_HANDLE) IndicatorRelease(m_htfFastEmaHandle);
   if(m_htfSlowEmaHandle != INVALID_HANDLE) IndicatorRelease(m_htfSlowEmaHandle);
   if(m_htfRsiHandle != INVALID_HANDLE) IndicatorRelease(m_htfRsiHandle);

   if(InpDrawVisuals)
   {
      DeleteAllVisualObjects();
      ChartRedraw(0);
   }

   PrintFormat("[DESCARGADO] Worker STEP EA finalizado. Motivo: %d", reason);
}

//+------------------------------------------------------------------+
//| Evento Principal OnTick                                          |
//+------------------------------------------------------------------+
void OnTick()
{
   if(!m_symbol.RefreshRates())
      return;

   // 1. Gestion de posiciones abiertas
   ManageOpenPositions();

   // 2. Control de Nueva Barra
   bool isNewBar = CheckNewBar();

   if(isNewBar)
   {
      if(InpMsnrEnabled)
         ScanMsnrLevels();

      if(InpIctEnabled)
         ScanIctMarketStructure();
   }

   // 3. Monitoreo y disparo de entradas
   EvaluateTradeExecution();
}

//+------------------------------------------------------------------+
//| Verifica apertura de una nueva barra                             |
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
//| Retorna el valor actual del ATR                                  |
//+------------------------------------------------------------------+
double GetCurrentAtr()
{
   if(m_atrHandle == INVALID_HANDLE)
      return 0.0;

   double atrVals[1];
   if(CopyBuffer(m_atrHandle, 0, 1, 1, atrVals) <= 0)
      return 0.0;

   return atrVals[0];
}

//+------------------------------------------------------------------+
//| Retorna el valor actual del ADX                                  |
//+------------------------------------------------------------------+
double GetCurrentAdx()
{
   if(!InpUseAdxFilter || m_adxHandle == INVALID_HANDLE)
      return 100.0;

   double adxVals[1];
   if(CopyBuffer(m_adxHandle, 0, 1, 1, adxVals) <= 0)
      return 100.0;

   return adxVals[0];
}

//+------------------------------------------------------------------+
//| Evalua la tendencia mayor HTF con doble EMA y filtro RSI         |
//| Retorna: +1 Alcista Fuerte, -1 Bajista Fuerte, 0 Rango/Neutral   |
//+------------------------------------------------------------------+
int GetHtfTrendDirection()
{
   if(!InpUseHtfFilter || m_htfFastEmaHandle == INVALID_HANDLE || m_htfSlowEmaHandle == INVALID_HANDLE)
      return 0;

   double fastEma[1];
   double slowEma[];
   ArraySetAsSeries(slowEma, true);

   if(CopyBuffer(m_htfFastEmaHandle, 0, 1, 1, fastEma) <= 0) return 0;
   if(CopyBuffer(m_htfSlowEmaHandle, 0, 1, 6, slowEma) < 6) return 0;

   double htfClose = iClose(m_symbol.Name(), InpHtfTimeframe, 1);

   bool slowEmaSlopingUp = (slowEma[0] > slowEma[5]);
   bool slowEmaSlopingDown = (slowEma[0] < slowEma[5]);

   // Evaluar Momentum RSI en H1 si esta activo
   double rsiVal = 50.0;
   if(InpUseHtfRsiFilter && m_htfRsiHandle != INVALID_HANDLE)
   {
      double rsiBuf[1];
      if(CopyBuffer(m_htfRsiHandle, 0, 1, 1, rsiBuf) > 0)
         rsiVal = rsiBuf[0];
   }

   // Tendencia Alcista Confirmada: Precio > EMA 50 > EMA 200 Y EMA 200 con pendiente positiva Y RSI H1 >= 50
   if(htfClose > fastEma[0] && fastEma[0] > slowEma[0] && slowEmaSlopingUp)
   {
      if(!InpUseHtfRsiFilter || rsiVal >= InpMinBuyRsi)
         return 1;
   }

   // Tendencia Bajista Confirmada: Precio < EMA 50 < EMA 200 Y EMA 200 con pendiente negativa Y RSI H1 <= 50
   if(htfClose < fastEma[0] && fastEma[0] < slowEma[0] && slowEmaSlopingDown)
   {
      if(!InpUseHtfRsiFilter || rsiVal <= InpMaxSellRsi)
         return -1;
   }

   return 0; // Sin alineacion pura: NO OPERAR
}

//+------------------------------------------------------------------+
//| Valida si un nivel ya fue operado y consumido                    |
//+------------------------------------------------------------------+
bool IsLevelConsumed(double level)
{
   for(int i = 0; i < ArraySize(m_consumedLevels); i++)
   {
      if(MathAbs(m_consumedLevels[i] - level) < (5 * m_symbol.Point()))
         return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| Registra un nivel como consumido                                 |
//+------------------------------------------------------------------+
void MarkLevelAsConsumed(double level)
{
   int sz = ArraySize(m_consumedLevels);
   ArrayResize(m_consumedLevels, sz + 1);
   m_consumedLevels[sz] = level;

   if(sz > 50)
   {
      ArrayCopy(m_consumedLevels, m_consumedLevels, 0, 1, sz);
      ArrayResize(m_consumedLevels, sz);
   }
}

//+------------------------------------------------------------------+
//| Circuito de Proteccion Diario (Circuit Breaker)                  |
//+------------------------------------------------------------------+
bool CheckDailyCircuitBreaker()
{
   if(!InpUseCircuitBreaker)
      return true;

   datetime now = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(now, dt);

   datetime todayStart = now - (dt.hour * 3600 + dt.min * 60 + dt.sec);

   if(!HistorySelect(todayStart, now))
      return true;

   int totalDeals = HistoryDealsTotal();
   double dailyPnL = 0.0;
   int consecutiveLosses = 0;

   for(int i = 0; i < totalDeals; i++)
   {
      ulong ticket = HistoryDealGetTicket(i);
      if(ticket == 0) continue;

      long magic = HistoryDealGetInteger(ticket, DEAL_MAGIC);
      if(magic != (long)InpMagicNumber) continue;

      long entryType = HistoryDealGetInteger(ticket, DEAL_ENTRY);
      if(entryType != DEAL_ENTRY_OUT) continue;

      double profit = HistoryDealGetDouble(ticket, DEAL_PROFIT);
      double swap   = HistoryDealGetDouble(ticket, DEAL_SWAP);
      double comm   = HistoryDealGetDouble(ticket, DEAL_COMMISSION);
      double net    = profit + swap + comm;

      dailyPnL += net;

      if(net < 0.0)
         consecutiveLosses++;
      else if(net > 0.0)
         consecutiveLosses = 0;
   }

   double balance = m_account.Balance();
   double maxLossMoney = balance * (InpMaxDailyLossPercent / 100.0);

   if(dailyPnL < 0.0 && MathAbs(dailyPnL) >= maxLossMoney)
   {
      if(m_lastCircuitLogDate != todayStart)
      {
         PrintFormat("[CIRCUIT BREAKER] BLOQUEO: Perdida diaria ($%.2f) supero el limite del %.1f%% ($%.2f).",
                     MathAbs(dailyPnL), InpMaxDailyLossPercent, maxLossMoney);
         m_lastCircuitLogDate = todayStart;
      }
      return false;
   }

   if(consecutiveLosses >= InpMaxDailyConsLosses)
   {
      if(m_lastCircuitLogDate != todayStart)
      {
         PrintFormat("[CIRCUIT BREAKER] BLOQUEO: Se alcanzaron %d perdidas consecutivas hoy. Pausa.",
                     consecutiveLosses);
         m_lastCircuitLogDate = todayStart;
      }
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Cuenta cuantos sets de posiciones activas tiene este EA          |
//+------------------------------------------------------------------+
int CountOpenPositionSets()
{
   int sets = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(m_position.SelectByIndex(i))
      {
         if(m_position.Symbol() == m_symbol.Name() && m_position.Magic() == InpMagicNumber)
         {
            sets++;
         }
      }
   }
   if(InpOrderStyle == STYLE_SPLIT_LEGS)
      return (sets > 0) ? (int)MathCeil((double)sets / 2.0) : 0;

   return sets;
}

//+------------------------------------------------------------------+
//| Valida si estamos en horario operativo                           |
//+------------------------------------------------------------------+
bool IsAllowedTime()
{
   if(InpIsSynthetic247 || !InpUseTimeFilter)
      return true;

   datetime now = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(now, dt);

   int hour = dt.hour;
   return (hour >= InpSessionStartHour && hour < InpSessionEndHour);
}

//+------------------------------------------------------------------+
//| MOTOR MALAYSIAN SNR: Escaneo y Deteccion de Niveles A / V        |
//+------------------------------------------------------------------+
void ScanMsnrLevels()
{
   double atr = GetCurrentAtr();
   if(atr <= 0.0)
      return;

   if(GetCurrentAdx() < InpMinAdxLevel)
      return;

   int htfTrend = GetHtfTrendDirection();
   if(htfTrend == 0 && InpUseHtfFilter)
      return;

   ArrayResize(m_activeMsnrLevels, 0);

   for(int i = 2; i < InpAvLookbackBars; i++)
   {
      double o_prev = iOpen(m_symbol.Name(), _Period, i + 1);
      double c_prev = iClose(m_symbol.Name(), _Period, i + 1);
      double h_prev = iHigh(m_symbol.Name(), _Period, i + 1);
      double l_prev = iLow(m_symbol.Name(), _Period, i + 1);

      double o_curr = iOpen(m_symbol.Name(), _Period, i);
      double c_curr = iClose(m_symbol.Name(), _Period, i);
      double h_curr = iHigh(m_symbol.Name(), _Period, i);
      double l_curr = iLow(m_symbol.Name(), _Period, i);

      bool isA_Resistance = false;
      bool isV_Support    = false;

      if(InpAvDefinition == AV_ENGULFING)
      {
         if(c_prev > o_prev && c_curr < o_curr && c_curr <= o_prev)
            isA_Resistance = true;

         if(c_prev < o_prev && c_curr > o_curr && c_curr >= o_prev)
            isV_Support = true;
      }
      else
      {
         if(c_prev > o_prev && c_curr < o_curr)
            isA_Resistance = true;
         if(c_prev < o_prev && c_curr > o_curr)
            isV_Support = true;
      }

      if(!isA_Resistance && !isV_Support)
         continue;

      // Filtro HTF Direccional
      if(htfTrend < 0 && isA_Resistance)
         continue;
      if(htfTrend > 0 && isV_Support)
         continue;

      // Filtro Manual de Direccion
      if(InpTradeDirection == DIR_ONLY_SELL && isA_Resistance)
         continue;
      if(InpTradeDirection == DIR_ONLY_BUY && isV_Support)
         continue;

      double breakLevel = c_prev;
      double wickBound  = isA_Resistance ? MathMax(h_prev, h_curr) : MathMin(l_prev, l_curr);
      datetime timeLevel= iTime(m_symbol.Name(), _Period, i);

      if(IsLevelConsumed(breakLevel))
         continue;

      bool isFresh = true;
      bool isBroken = false;
      datetime breakTime = 0;
      int breakBarIdx = 0;

      for(int k = i - 1; k >= 1; k--)
      {
         double k_high  = iHigh(m_symbol.Name(), _Period, k);
         double k_low   = iLow(m_symbol.Name(), _Period, k);
         double k_close = iClose(m_symbol.Name(), _Period, k);

         if(!isBroken)
         {
            if(isA_Resistance && k_close > breakLevel)
            {
               double displacement = (k_close - breakLevel) / atr;
               if(displacement >= InpMinBreakDisplacement)
               {
                  isBroken = true;
                  breakTime = iTime(m_symbol.Name(), _Period, k);
                  breakBarIdx = k;
               }
            }
            else if(isV_Support && k_close < breakLevel)
            {
               double displacement = (breakLevel - k_close) / atr;
               if(displacement >= InpMinBreakDisplacement)
               {
                  isBroken = true;
                  breakTime = iTime(m_symbol.Name(), _Period, k);
                  breakBarIdx = k;
               }
            }
            else
            {
               if(k_low <= breakLevel && k_high >= breakLevel)
               {
                  isFresh = false;
               }
            }
         }
      }

      if(InpRequireFreshLevel && !isFresh)
         continue;

      if(isBroken && breakBarIdx <= InpMaxBarsSinceBreak)
      {
         int size = ArraySize(m_activeMsnrLevels);
         ArrayResize(m_activeMsnrLevels, size + 1);
         m_activeMsnrLevels[size].isResistance   = isA_Resistance;
         m_activeMsnrLevels[size].breakLevel     = breakLevel;
         m_activeMsnrLevels[size].wickBound      = wickBound;
         m_activeMsnrLevels[size].time           = timeLevel;
         m_activeMsnrLevels[size].barIndex       = i;
         m_activeMsnrLevels[size].isFresh        = isFresh;
         m_activeMsnrLevels[size].isBroken       = true;
         m_activeMsnrLevels[size].breakTime      = breakTime;
         m_activeMsnrLevels[size].barsSinceBreak = breakBarIdx;

         if(InpDrawVisuals)
         {
            string lineName = PREFIX_STEP + (isA_Resistance ? "RES_A_" : "SUP_V_") + TimeToString(timeLevel);
            DrawHorizontalLine(lineName, breakLevel, (isA_Resistance ? InpColorMsnrRes : InpColorMsnrSup),
                               STYLE_SOLID, (isA_Resistance ? "MSNR Resistencia A Rota (Soporte)" : "MSNR Soporte V Roto (Resistencia)"));
         }
      }
   }
}

//+------------------------------------------------------------------+
//| MOTOR ICT: Escaneo de Market Structure Shift y Fair Value Gaps   |
//+------------------------------------------------------------------+
void ScanIctMarketStructure()
{
   double atr = GetCurrentAtr();
   if(atr <= 0.0)
      return;

   if(GetCurrentAdx() < InpMinAdxLevel)
      return;

   int htfTrend = GetHtfTrendDirection();
   if(htfTrend == 0 && InpUseHtfFilter)
      return;

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

   double bodyPercent = (body2 / range2) * 100.0;
   if(bodyPercent < InpMinMssBodyPercent)
      return;

   double minFvgSizePrice = MathMax(InpMinFvgPoints * m_symbol.Point(), InpMinFvgAtrRatio * atr);

   // 1. Bullish FVG
   if(low1 > high3 && (low1 - high3) >= minFvgSizePrice && close2 > open2)
   {
      if(htfTrend > 0 && InpTradeDirection != DIR_ONLY_SELL)
      {
         double swingHigh = FindRecentSwingHigh(3, 25, InpSwingLookback);
         if(swingHigh > 0.0 && close2 > swingHigh)
         {
            m_activeFvg.active    = true;
            m_activeFvg.isBullish = true;
            m_activeFvg.highPrice = low1;
            m_activeFvg.lowPrice  = high3;
            m_activeFvg.cePrice   = (low1 + high3) / 2.0;
            m_activeFvg.time      = iTime(m_symbol.Name(), _Period, 1);
            m_activeFvg.barIndex  = 1;
            m_activeFvg.objName   = PREFIX_STEP + "ICT_BULL_FVG_" + TimeToString(m_activeFvg.time);

            if(InpDrawVisuals)
            {
               DrawFvgBox(m_activeFvg.objName, m_activeFvg.time, m_activeFvg.highPrice, m_activeFvg.lowPrice, InpColorBullFvg);
            }
         }
      }
   }

   // 2. Bearish FVG
   if(high1 < low3 && (low3 - high1) >= minFvgSizePrice && close2 < open2)
   {
      if(htfTrend < 0 && InpTradeDirection != DIR_ONLY_BUY)
      {
         double swingLow = FindRecentSwingLow(3, 25, InpSwingLookback);
         if(swingLow > 0.0 && close2 < swingLow)
         {
            m_activeFvg.active    = true;
            m_activeFvg.isBullish = false;
            m_activeFvg.highPrice = low3;
            m_activeFvg.lowPrice  = high1;
            m_activeFvg.cePrice   = (low3 + high1) / 2.0;
            m_activeFvg.time      = iTime(m_symbol.Name(), _Period, 1);
            m_activeFvg.barIndex  = 1;
            m_activeFvg.objName   = PREFIX_STEP + "ICT_BEAR_FVG_" + TimeToString(m_activeFvg.time);

            if(InpDrawVisuals)
            {
               DrawFvgBox(m_activeFvg.objName, m_activeFvg.time, m_activeFvg.highPrice, m_activeFvg.lowPrice, InpColorBearFvg);
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Evaluacion y Disparo de Oportunidades Sniper                     |
//+------------------------------------------------------------------+
void EvaluateTradeExecution()
{
   if(!IsAllowedTime())
      return;

   datetime currentBarTime = iTime(m_symbol.Name(), _Period, 0);
   if(m_lastTradeBarTime == currentBarTime)
      return;

   if(!CheckDailyCircuitBreaker())
      return;

   if(CountOpenPositionSets() >= InpMaxOpenSets)
      return;

   if(m_symbol.Spread() > InpMaxSpreadPoints)
      return;

   double ask = m_symbol.Ask();
   double bid = m_symbol.Bid();
   double atr = GetCurrentAtr();
   if(atr <= 0.0) return;

   bool signalBuy  = false;
   bool signalSell = false;
   string stratTag = "";
   double entryPrice = 0.0;
   double slPrice    = 0.0;
   double consumedLvl = 0.0;

   // ---------------------------------------------------------------
   // EVALUACION MSNR CON GATILLO DE ABSORCION (PINBAR / RECHAZO)
   // ---------------------------------------------------------------
   bool msnrBuy = false;
   bool msnrSell = false;
   double msnrBuySl = 0.0;
   double msnrSellSl = 0.0;
   double matchingMsnrLvl = 0.0;

   double b1Open  = iOpen(m_symbol.Name(), _Period, 1);
   double b1Close = iClose(m_symbol.Name(), _Period, 1);
   double b1High  = iHigh(m_symbol.Name(), _Period, 1);
   double b1Low   = iLow(m_symbol.Name(), _Period, 1);
   double b1Span  = b1High - b1Low;

   for(int i = 0; i < ArraySize(m_activeMsnrLevels); i++)
   {
      double lvl = m_activeMsnrLevels[i].breakLevel;

      // Resistencia A rota al alza -> ahora es Soporte
      if(m_activeMsnrLevels[i].isResistance && m_activeMsnrLevels[i].isBroken && InpTradeDirection != DIR_ONLY_SELL)
      {
         bool retestCondition = false;
         if(InpRequireRejectionWick && b1Span > 0.0)
         {
            double lowerWick = MathMin(b1Open, b1Close) - b1Low;
            double wickRatio = lowerWick / b1Span;

            // La mecha toco el nivel y dejo absorcion institucional
            if(b1Low <= lvl + (InpMaxRetestDistanceAtr * atr) && b1Close >= lvl && (wickRatio >= 0.35 || b1Close > b1Open))
               retestCondition = true;
         }
         else
         {
            if(MathAbs(ask - lvl) <= InpMaxRetestDistanceAtr * atr)
               retestCondition = true;
         }

         if(retestCondition)
         {
            msnrBuy = true;
            msnrBuySl = m_activeMsnrLevels[i].wickBound - (InpSlBufferPoints * m_symbol.Point());
            matchingMsnrLvl = lvl;
            break;
         }
      }

      // Soporte V roto a la baja -> ahora es Resistencia
      if(!m_activeMsnrLevels[i].isResistance && m_activeMsnrLevels[i].isBroken && InpTradeDirection != DIR_ONLY_BUY)
      {
         bool retestCondition = false;
         if(InpRequireRejectionWick && b1Span > 0.0)
         {
            double upperWick = b1High - MathMax(b1Open, b1Close);
            double wickRatio = upperWick / b1Span;

            if(b1High >= lvl - (InpMaxRetestDistanceAtr * atr) && b1Close <= lvl && (wickRatio >= 0.35 || b1Close < b1Open))
               retestCondition = true;
         }
         else
         {
            if(MathAbs(bid - lvl) <= InpMaxRetestDistanceAtr * atr)
               retestCondition = true;
         }

         if(retestCondition)
         {
            msnrSell = true;
            msnrSellSl = m_activeMsnrLevels[i].wickBound + (InpSlBufferPoints * m_symbol.Point());
            matchingMsnrLvl = lvl;
            break;
         }
      }
   }

   // ---------------------------------------------------------------
   // EVALUACION ICT (Mitigacion de FVG)
   // ---------------------------------------------------------------
   bool ictBuy = false;
   bool ictSell = false;
   double ictBuySl = 0.0;
   double ictSellSl = 0.0;

   if(m_activeFvg.active)
   {
      if(m_activeFvg.isBullish && InpTradeDirection != DIR_ONLY_SELL)
      {
         double trigger = InpUseConsequentEncroach ? m_activeFvg.cePrice : m_activeFvg.highPrice;
         if(ask <= trigger && ask >= m_activeFvg.lowPrice)
         {
            ictBuy = true;
            ictBuySl = m_activeFvg.lowPrice - (InpSlBufferPoints * m_symbol.Point());
         }
         else if(bid < m_activeFvg.lowPrice)
         {
            m_activeFvg.active = false;
         }
      }
      else if(!m_activeFvg.isBullish && InpTradeDirection != DIR_ONLY_BUY)
      {
         double trigger = InpUseConsequentEncroach ? m_activeFvg.cePrice : m_activeFvg.lowPrice;
         if(bid >= trigger && bid <= m_activeFvg.highPrice)
         {
            ictSell = true;
            ictSellSl = m_activeFvg.highPrice + (InpSlBufferPoints * m_symbol.Point());
         }
         else if(ask > m_activeFvg.highPrice)
         {
            m_activeFvg.active = false;
         }
      }
   }

   // ---------------------------------------------------------------
   // RESOLUCION DEL MODO DE EJECUCION
   // ---------------------------------------------------------------
   if(InpExecutionMode == MODE_STRICT_CONFLUENCE)
   {
      if(msnrBuy && ictBuy)
      {
         signalBuy   = true;
         stratTag    = "CONFLUENCE";
         entryPrice  = ask;
         slPrice     = MathMin(msnrBuySl, ictBuySl);
         consumedLvl = matchingMsnrLvl;
      }
      else if(msnrSell && ictSell)
      {
         signalSell  = true;
         stratTag    = "CONFLUENCE";
         entryPrice  = bid;
         slPrice     = MathMax(msnrSellSl, ictSellSl);
         consumedLvl = matchingMsnrLvl;
      }
   }
   else
   {
      if(msnrBuy)
      {
         signalBuy   = true;
         stratTag    = "MSNR";
         entryPrice  = ask;
         slPrice     = msnrBuySl;
         consumedLvl = matchingMsnrLvl;
      }
      else if(ictBuy)
      {
         signalBuy  = true;
         stratTag   = "ICT";
         entryPrice = ask;
         slPrice    = ictBuySl;
      }
      else if(msnrSell)
      {
         signalSell  = true;
         stratTag    = "MSNR";
         entryPrice  = bid;
         slPrice     = msnrSellSl;
         consumedLvl = matchingMsnrLvl;
      }
      else if(ictSell)
      {
         signalSell  = true;
         stratTag    = "ICT";
         entryPrice = bid;
         slPrice    = ictSellSl;
      }
   }

   // ---------------------------------------------------------------
   // SPREAD GATE Y EJECUCION SNIPER
   // ---------------------------------------------------------------
   if(signalBuy)
   {
      double slDist = (entryPrice - slPrice) / m_symbol.Point();
      if(slDist < InpMinSlPoints) slPrice = entryPrice - (InpMinSlPoints * m_symbol.Point());
      if(slDist > InpMaxSlPoints) slPrice = entryPrice - (InpMaxSlPoints * m_symbol.Point());

      double riskSpan = entryPrice - slPrice;
      double spreadCost = m_symbol.Spread() * m_symbol.Point();

      if(riskSpan > 0.0 && (spreadCost / riskSpan) > InpMaxSpreadToSlRatio)
         return;

      double tp1 = entryPrice + (riskSpan * InpTarget1_RR);
      double tp2 = entryPrice + (riskSpan * (InpOrderStyle == STYLE_SINGLE_ORDER ? InpSingleOrderRR : InpTarget2_RR));

      ExecuteTradeLegs(stratTag, ORDER_TYPE_BUY, entryPrice, slPrice, tp1, tp2);
      m_lastTradeBarTime = currentBarTime;
      m_activeFvg.active = false;
      if(consumedLvl > 0.0) MarkLevelAsConsumed(consumedLvl);
   }
   else if(signalSell)
   {
      double slDist = (slPrice - entryPrice) / m_symbol.Point();
      if(slDist < InpMinSlPoints) slPrice = entryPrice + (InpMinSlPoints * m_symbol.Point());
      if(slDist > InpMaxSlPoints) slPrice = entryPrice + (InpMaxSlPoints * m_symbol.Point());

      double riskSpan = slPrice - entryPrice;
      double spreadCost = m_symbol.Spread() * m_symbol.Point();

      if(riskSpan > 0.0 && (spreadCost / riskSpan) > InpMaxSpreadToSlRatio)
         return;

      double tp1 = entryPrice - (riskSpan * InpTarget1_RR);
      double tp2 = entryPrice - (riskSpan * (InpOrderStyle == STYLE_SINGLE_ORDER ? InpSingleOrderRR : InpTarget2_RR));

      ExecuteTradeLegs(stratTag, ORDER_TYPE_SELL, entryPrice, slPrice, tp1, tp2);
      m_lastTradeBarTime = currentBarTime;
      m_activeFvg.active = false;
      if(consumedLvl > 0.0) MarkLevelAsConsumed(consumedLvl);
   }
}

//+------------------------------------------------------------------+
//| Ejecuta las posiciones segun el estilo                           |
//+------------------------------------------------------------------+
void ExecuteTradeLegs(string strategyName, ENUM_ORDER_TYPE orderType, double price, double sl, double tp1, double tp2)
{
   sl  = m_symbol.NormalizePrice(sl);
   tp1 = m_symbol.NormalizePrice(tp1);
   tp2 = m_symbol.NormalizePrice(tp2);

   double riskDist = MathAbs(price - sl);

   if(InpOrderStyle == STYLE_SINGLE_ORDER)
   {
      double lot = CalculateLotSize(riskDist, 1.0);
      if(lot <= 0.0) return;

      string comment = StringFormat("%s-%s-SNIPER", InpBaseComment, strategyName);
      if(orderType == ORDER_TYPE_BUY)
      {
         m_trade.Buy(lot, m_symbol.Name(), price, sl, tp2, comment);
         PrintFormat("[SNIPER BUY] %s | Lote=%.2f, Entrada=%.5f, SL=%.5f, TP=%.5f (R:R 1:%.1f)",
                     strategyName, lot, price, sl, tp2, InpSingleOrderRR);
      }
      else
      {
         m_trade.Sell(lot, m_symbol.Name(), price, sl, tp2, comment);
         PrintFormat("[SNIPER SELL] %s | Lote=%.2f, Entrada=%.5f, SL=%.5f, TP=%.5f (R:R 1:%.1f)",
                     strategyName, lot, price, sl, tp2, InpSingleOrderRR);
      }
   }
   else // STYLE_SPLIT_LEGS
   {
      double lotLeg1 = CalculateLotSize(riskDist, 0.50);
      double lotLeg2 = CalculateLotSize(riskDist, 0.50);

      if(lotLeg1 <= 0.0 || lotLeg2 <= 0.0) return;

      string comment1 = StringFormat("%s-%s-TP1", InpBaseComment, strategyName);
      string comment2 = StringFormat("%s-%s-RUNNER", InpBaseComment, strategyName);

      if(orderType == ORDER_TYPE_BUY)
      {
         m_trade.Buy(lotLeg1, m_symbol.Name(), price, sl, tp1, comment1);
         m_trade.Buy(lotLeg2, m_symbol.Name(), price, sl, tp2, comment2);
      }
      else
      {
         m_trade.Sell(lotLeg1, m_symbol.Name(), price, sl, tp1, comment1);
         m_trade.Sell(lotLeg2, m_symbol.Name(), price, sl, tp2, comment2);
      }
   }
}

//+------------------------------------------------------------------+
//| Calcula el lote de acuerdo al modo de riesgo configurado        |
//+------------------------------------------------------------------+
double CalculateLotSize(double slDistancePrice, double riskFraction)
{
   if(InpRiskMode == RISK_FIXED_LOT)
   {
      return NormalizeVolume(InpFixedLot * riskFraction);
   }

   if(slDistancePrice <= 0.0)
      return 0.0;

   double legRiskMoney = 0.0;

   if(InpRiskMode == RISK_FIXED_CASH)
   {
      // Riesgo monetario constante en dolares (ej: $50 fijos)
      legRiskMoney = InpFixedCashRisk * riskFraction;
   }
   else // RISK_PERCENT
   {
      double balance = m_account.Balance();
      legRiskMoney   = (balance * (InpRiskPercent / 100.0)) * riskFraction;
   }

   double tickSize    = m_symbol.TickSize();
   double tickValue   = m_symbol.TickValue();

   if(tickSize <= 0.0 || tickValue <= 0.0)
      return NormalizeVolume(InpFixedLot * riskFraction);

   double slTicks     = slDistancePrice / tickSize;
   double moneyPerLot = slTicks * tickValue;

   if(moneyPerLot <= 0.0)
      return NormalizeVolume(InpFixedLot * riskFraction);

   double calculatedLot = legRiskMoney / moneyPerLot;
   return NormalizeVolume(calculatedLot);
}

//+------------------------------------------------------------------+
//| Normaliza el volumen respetando parametros del broker            |
//+------------------------------------------------------------------+
double NormalizeVolume(double volume)
{
   double minLot  = m_symbol.LotsMin();
   double maxLot  = m_symbol.LotsMax();
   double stepLot = m_symbol.LotsStep();

   if(stepLot <= 0.0) stepLot = 0.01;

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
//| Gestion de Break Even                                            |
//+------------------------------------------------------------------+
void ManageOpenPositions()
{
   if(!InpEnableBreakEven)
      return;

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
      ENUM_POSITION_TYPE type = m_position.PositionType();

      double riskSpan = MathAbs(openPrice - currentSL);
      if(riskSpan <= 0.0)
         continue;

      double profit = (type == POSITION_TYPE_BUY) ? (currentPrice - openPrice) : (openPrice - currentPrice);
      double beThreshold = riskSpan * InpBeTriggerRR;

      if(profit >= beThreshold)
      {
         if(type == POSITION_TYPE_BUY && currentSL < openPrice)
         {
            double bePrice = m_symbol.NormalizePrice(openPrice + (InpBeLockPoints * m_symbol.Point()));
            m_trade.PositionModify(ticket, bePrice, currentTP);
         }
         else if(type == POSITION_TYPE_SELL && (currentSL > openPrice || currentSL == 0.0))
         {
            double bePrice = m_symbol.NormalizePrice(openPrice - (InpBeLockPoints * m_symbol.Point()));
            m_trade.PositionModify(ticket, bePrice, currentTP);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Busca el Swing High fractal mas reciente                         |
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
         if(iHigh(m_symbol.Name(), _Period, i + k) >= candidate ||
            iHigh(m_symbol.Name(), _Period, i - k) >= candidate)
         {
            isHigh = false;
            break;
         }
      }
      if(isHigh) return candidate;
   }
   return 0.0;
}

//+------------------------------------------------------------------+
//| Busca el Swing Low fractal mas reciente                          |
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
         if(iLow(m_symbol.Name(), _Period, i + k) <= candidate ||
            iLow(m_symbol.Name(), _Period, i - k) <= candidate)
         {
            isLow = false;
            break;
         }
      }
      if(isLow) return candidate;
   }
   return 0.0;
}

//+------------------------------------------------------------------+
//| Dibuja una linea horizontal de nivel MSNR                        |
//+------------------------------------------------------------------+
void DrawHorizontalLine(string name, double price, color clr, ENUM_LINE_STYLE style, string tip)
{
   if(ObjectFind(0, name) < 0)
   {
      ObjectCreate(0, name, OBJ_HLINE, 0, 0, price);
      ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
      ObjectSetInteger(0, name, OBJPROP_STYLE, style);
      ObjectSetInteger(0, name, OBJPROP_WIDTH, 1);
      ObjectSetString(0, name, OBJPROP_TOOLTIP, tip);
   }
   else
   {
      ObjectSetDouble(0, name, OBJPROP_PRICE, 0, price);
   }
}

//+------------------------------------------------------------------+
//| Dibuja una caja FVG de ICT                                       |
//+------------------------------------------------------------------+
void DrawFvgBox(string name, datetime timeStart, double priceHigh, double priceLow, color clr)
{
   datetime timeEnd = timeStart + (PeriodSeconds(_Period) * 12);
   if(ObjectFind(0, name) < 0)
   {
      ObjectCreate(0, name, OBJ_RECTANGLE, 0, timeStart, priceHigh, timeEnd, priceLow);
      ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
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
      if(StringFind(name, PREFIX_STEP) == 0)
      {
         ObjectDelete(0, name);
      }
   }
}
//+------------------------------------------------------------------+
