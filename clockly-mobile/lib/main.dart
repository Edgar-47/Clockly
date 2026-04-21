import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/date_symbol_data_local.dart';

import 'app.dart';
import 'core/constants/api_constants.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  ApiConstants.validateBaseUrl();
  await initializeDateFormatting('es', null);
  runApp(const ProviderScope(child: ClocklyApp()));
}
