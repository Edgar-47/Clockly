import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../shared/widgets/app_button.dart';
import '../../../shared/widgets/app_text_field.dart';
import '../../../shared/widgets/brand_logo.dart';
import '../../../shared/widgets/premium_components.dart';
import '../providers/auth_provider.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _identifierController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _identifierController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    await ref.read(authProvider.notifier).login(
          identifier: _identifierController.text.trim(),
          password: _passwordController.text,
        );
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final isLoading =
        authState.isLoading || (authState.valueOrNull?.loading ?? false);
    final error = authState.error?.toString() ?? authState.valueOrNull?.error;

    return Scaffold(
      body: ClocklyBackground(
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(22, 24, 22, 30),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 430),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    _HeroHeader(),
                    const SizedBox(height: AppSpacing.x3),
                    PremiumCard(
                      padding: const EdgeInsets.all(AppSpacing.x2),
                      child: Form(
                        key: _formKey,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Text(
                              'Accede a tu jornada',
                              style: Theme.of(context).textTheme.headlineMedium,
                            ),
                            const SizedBox(height: 6),
                            Text(
                              'Usa tu usuario, email o DNI para fichar y revisar tus registros.',
                              style: Theme.of(context).textTheme.bodyMedium,
                            ),
                            if (error != null && error.isNotEmpty) ...[
                              const SizedBox(height: AppSpacing.lg),
                              _ErrorBanner(message: error),
                            ],
                            const SizedBox(height: AppSpacing.x2),
                            AppTextField(
                              label: 'Usuario o DNI',
                              controller: _identifierController,
                              hint: 'tu@empresa.com',
                              prefixIcon: Icons.person_outline_rounded,
                              keyboardType: TextInputType.emailAddress,
                              autofocus: true,
                              onSubmitted: (_) =>
                                  FocusScope.of(context).nextFocus(),
                              validator: (v) {
                                if (v == null || v.trim().isEmpty) {
                                  return 'Introduce tu usuario o DNI';
                                }
                                return null;
                              },
                            ),
                            const SizedBox(height: AppSpacing.lg),
                            AppTextField(
                              label: 'Contraseña',
                              controller: _passwordController,
                              prefixIcon: Icons.lock_outline_rounded,
                              obscureText: true,
                              onSubmitted: (_) => _submit(),
                              validator: (v) {
                                if (v == null || v.isEmpty) {
                                  return 'Introduce tu contraseña';
                                }
                                if (v.length < 4) {
                                  return 'Contraseña demasiado corta';
                                }
                                return null;
                              },
                            ),
                            const SizedBox(height: AppSpacing.x2),
                            AppButton(
                              label: 'Iniciar sesión',
                              onPressed: isLoading ? null : _submit,
                              loading: isLoading,
                              icon: Icons.arrow_forward_rounded,
                              size: AppButtonSize.large,
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: AppSpacing.xl),
                    const _BusinessHint(),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _HeroHeader extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const ClocklyBrandLogo(
          variant: ClocklyLogoVariant.horizontal,
          markSize: 46,
          wordmarkSize: 28,
          inverse: true,
        ),
        const SizedBox(height: AppSpacing.x3),
        Text(
          'Control horario claro para equipos que se mueven rápido.',
          style: Theme.of(context).textTheme.displayMedium?.copyWith(
                color: AppColors.paper,
                height: 1.04,
              ),
        ),
        const SizedBox(height: AppSpacing.md),
        Text(
          'Fichajes, sesiones y registros conectados a tu negocio.',
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: Colors.white.withOpacity(0.68),
                height: 1.4,
              ),
        ),
      ],
    );
  }
}

class _BusinessHint extends StatelessWidget {
  const _BusinessHint();

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Row(
        children: [
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              color: AppColors.cobalt.withOpacity(0.22),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(
              Icons.storefront_rounded,
              color: AppColors.cobaltLight,
              size: 18,
            ),
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Text(
              'El negocio activo se sincroniza automáticamente tras iniciar sesión.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Colors.white.withOpacity(0.66),
                    height: 1.3,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: AppColors.roseSoft,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.rose.withOpacity(0.22)),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline_rounded,
              color: AppColors.rose, size: 18),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(
                color: AppColors.rose,
                fontSize: 13,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
