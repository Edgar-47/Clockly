import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/app_state.dart';
import 'core/network/api_client.dart';
import 'core/storage/session_storage.dart';
import 'repositories/clockly_repository.dart';
import 'screens/login_screen.dart';
import 'screens/shell_screen.dart';

void main() {
  final apiClient = ApiClient();
  final repository = ClocklyRepository(
    apiClient: apiClient,
    sessionStorage: const SessionStorage(),
  );
  runApp(ClocklyApp(repository: repository));
}

class ClocklyApp extends StatelessWidget {
  const ClocklyApp({super.key, required this.repository});

  final ClocklyRepository repository;

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AppState(repository)..restore(),
      child: MaterialApp(
        title: 'ClockLy',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF2563EB)),
          useMaterial3: true,
        ),
        home: Consumer<AppState>(
          builder: (context, state, _) {
            if (state.loading && state.session == null) {
              return const Scaffold(
                body: Center(child: CircularProgressIndicator()),
              );
            }
            return state.isAuthenticated ? const ShellScreen() : const LoginScreen();
          },
        ),
      ),
    );
  }
}
