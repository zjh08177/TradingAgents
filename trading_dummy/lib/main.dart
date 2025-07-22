import 'package:flutter/material.dart';
import 'data/repositories/config_service.dart';
import 'presentation/pages/trading_analysis_page.dart';
import 'shared/constants/app_constants.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize configuration service
  await ConfigService.instance.initialize();
  
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: AppConstants.appName,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
        useMaterial3: true,
      ),
      home: const TradingAnalysisPage(),
    );
  }
}
